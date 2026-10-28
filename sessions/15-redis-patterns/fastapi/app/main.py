import os
import time
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session, r
from app.models import Film
from app.patterns import (
    allow_request,
    customer_key,
    get_customer,
    leaderboard_key,
    record_rental,
    run_exclusively,
    update_customer,
)

app = FastAPI(title="Session 15: Redis data structures and patterns")

RATE_LIMIT = int(os.getenv("RATE_LIMIT", "10"))


# --- String as a counter ----------------------------------------------------

@app.post("/films/{film_id}/views")
def add_view(film_id: int):
    # INCR is atomic: concurrent requests never lose a view.
    return {"film_id": film_id, "views": r.incr(f"film:{film_id}:views")}


@app.get("/films/{film_id}/views")
def get_views(film_id: int):
    return {"film_id": film_id, "views": int(r.get(f"film:{film_id}:views") or 0)}


# --- Hash -------------------------------------------------------------------

@app.post("/films/{film_id}/hash")
def store_film_hash(film_id: int, session: Session = Depends(get_session)):
    """Copies a few film fields from PostgreSQL into a hash: one key, several fields."""
    film = session.get(Film, film_id)
    if film is None:
        raise HTTPException(404, "Film not found")
    r.hset(f"film:{film_id}", mapping={"title": film.title, "rate": str(film.rental_rate)})
    return r.hgetall(f"film:{film_id}")


@app.get("/films/{film_id}/hash")
def get_film_hash(film_id: int):
    return r.hgetall(f"film:{film_id}")


# --- Set --------------------------------------------------------------------

@app.post("/visitors/{customer_id}")
def add_visitor(customer_id: int):
    """A set keeps each member once: a customer visiting twice counts once."""
    key = f"visitors:{date.today().isoformat()}"
    r.sadd(key, f"customer:{customer_id}")
    return {"day": key.split(":")[1], "unique_visitors": r.scard(key)}


@app.get("/visitors")
def count_visitors(day: date | None = None):
    day = day or date.today()
    return {"day": day.isoformat(), "unique_visitors": r.scard(f"visitors:{day.isoformat()}")}


# --- Sorted set, plus the rate limit ------------------------------------------

def rate_limited(request: Request):
    """Fixed window: RATE_LIMIT requests per client per clock minute."""
    allowed, count = allow_request(request.client.host, RATE_LIMIT)
    if not allowed:
        raise HTTPException(
            429,
            f"Rate limit of {RATE_LIMIT} per minute exceeded ({count} requests)",
            headers={"Retry-After": str(60 - int(time.time()) % 60)},
        )


@app.get("/search", dependencies=[Depends(rate_limited)])
def search(q: str = Query(min_length=1), session: Session = Depends(get_session)):
    term = q.strip().lower()
    r.zincrby("search:terms", 1, term)
    films = session.scalars(
        select(Film.title).where(Film.title.ilike(f"%{term}%")).order_by(Film.title).limit(10)
    ).all()
    return {"q": term, "films": films}


@app.get("/search/popular")
def popular_terms(limit: int = Query(5, ge=1, le=50)):
    # ZRANGE ... REV WITHSCORES: highest score first.
    terms = r.zrange("search:terms", 0, limit - 1, desc=True, withscores=True)
    return [{"term": t, "searches": int(s)} for t, s in terms]


# --- Sorted set as a weekly leaderboard ---------------------------------------

WEEK = Query(None, pattern=r"^\d{4}-W\d{2}$", examples=["2026-W41"])


def week_key(week: str | None) -> str:
    return f"leaderboard:customers:{week}" if week else leaderboard_key()


@app.post("/leaderboard/customers/{customer_id}")
def add_rental_to_leaderboard(customer_id: int = Path(ge=1)):
    """Records one rental for the customer in this week's leaderboard."""
    key, score = record_rental(customer_id)
    member = f"customer:{customer_id}"
    return {"key": key, "member": member, "rentals": int(score), "rank": r.zrevrank(key, member) + 1}


@app.get("/leaderboard/customers")
def top_customers(week: str | None = WEEK, limit: int = Query(10, ge=1, le=100)):
    """ZRANGE key 0 9 REV WITHSCORES (the same as ZREVRANGE key 0 9 WITHSCORES): the top 10."""
    key = week_key(week)
    top = r.zrange(key, 0, limit - 1, desc=True, withscores=True)
    return {
        "key": key,
        "ttl": r.ttl(key),
        "top": [{"rank": i, "member": m, "rentals": int(s)} for i, (m, s) in enumerate(top, start=1)],
    }


@app.get("/leaderboard/customers/{customer_id}")
def customer_rank(customer_id: int, week: str | None = WEEK):
    """ZREVRANK counts from 0 for the highest score; None if the customer has no rental this week."""
    key, member = week_key(week), f"customer:{customer_id}"
    rank = r.zrevrank(key, member)
    if rank is None:
        raise HTTPException(404, f"{member} is not in {key}")
    return {"key": key, "member": member, "rank": rank + 1, "rentals": int(r.zscore(key, member))}


# --- Cache-aside ------------------------------------------------------------

class CustomerChanges(BaseModel):
    first_name: str | None = Field(None, min_length=1)
    last_name: str | None = Field(None, min_length=1)
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+$")


@app.get("/customers/{customer_id}")
def read_customer(customer_id: int, session: Session = Depends(get_session)):
    customer, cache = get_customer(session, customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    return {"cache": cache, "ttl": r.ttl(customer_key(customer_id)), "customer": customer}


@app.patch("/customers/{customer_id}")
def patch_customer(customer_id: int, body: CustomerChanges, session: Session = Depends(get_session)):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Nothing to change")
    if not update_customer(session, customer_id, changes):
        raise HTTPException(404, "Customer not found")
    return {"updated": changes, "cache_key_deleted": customer_key(customer_id)}


# --- Lock -------------------------------------------------------------------

@app.post("/jobs/nightly-export")
def nightly_export(seconds: float = Query(5, ge=0, le=30)):
    """Call it twice within a few seconds: the second call finds the lock taken."""
    ran = run_exclusively("nightly-export", lambda: time.sleep(seconds))
    if not ran:
        raise HTTPException(409, "nightly-export is already running")
    return {"ran": True, "seconds": seconds}
