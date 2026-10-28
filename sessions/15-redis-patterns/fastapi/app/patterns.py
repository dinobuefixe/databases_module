"""The patterns from the tutorial: cache-aside, a lock with safe release, a rate limit, a weekly leaderboard."""

import json
import time
import uuid
from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.db import r
from app.models import Customer

CACHE_TTL = 300  # seconds


# --- Cache-aside ------------------------------------------------------------

def customer_key(customer_id: int) -> str:
    return f"cache:customer:{customer_id}"


def load_customer_from_postgres(session: Session, customer_id: int) -> dict | None:
    c = session.get(Customer, customer_id)
    if c is None:
        return None
    return {"customer_id": c.customer_id, "first_name": c.first_name, "last_name": c.last_name, "email": c.email}


def get_customer(session: Session, customer_id: int) -> tuple[dict | None, str]:
    """Returns the customer and "hit" or "miss"."""
    key = customer_key(customer_id)
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached), "hit"
    data = load_customer_from_postgres(session, customer_id)
    if data is not None:
        # The TTL bounds how long a stale copy can survive if an invalidation is ever missed.
        r.set(key, json.dumps(data), ex=CACHE_TTL)
    return data, "miss"


def update_customer(session: Session, customer_id: int, changes: dict) -> bool:
    """Writes PostgreSQL first, then deletes the cache key. The next read refills it."""
    with session.begin():
        c = session.get(Customer, customer_id)
        if c is None:
            return False
        for field, value in changes.items():
            setattr(c, field, value)
    r.delete(customer_key(customer_id))
    return True


# --- Lock with expiry and safe release --------------------------------------

# Deletes the lock only if it still holds our token. GET and DEL run together inside
# Redis, so no other client can take the lock between the check and the delete.
release = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
""")


def run_exclusively(name: str, job: Callable[[], None], ttl: int = 60) -> bool:
    token = str(uuid.uuid4())
    # SET NX EX: only one client gets the key; it expires on its own if that client crashes.
    if not r.set(f"lock:{name}", token, nx=True, ex=ttl):
        return False
    try:
        job()
    finally:
        release(keys=[f"lock:{name}"], args=[token])
    return True


# --- Fixed-window rate limit ------------------------------------------------

def allow_request(client_id: str, limit: int = 10) -> tuple[bool, int]:
    """Returns whether the request is allowed and the count in the current window."""
    window = int(time.time() // 60)
    key = f"ratelimit:{client_id}:{window}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    count, _ = pipe.execute()
    return count <= limit, count


# --- Weekly leaderboard -------------------------------------------------------

# Two weeks from the first write, so last week's board can still be read during this week.
LEADERBOARD_TTL = 14 * 24 * 3600


def leaderboard_key(day: date | None = None) -> str:
    """One sorted set per ISO week: leaderboard:customers:2026-W41."""
    year, week, _ = (day or date.today()).isocalendar()
    return f"leaderboard:customers:{year}-W{week:02d}"


def record_rental(customer_id: int) -> tuple[str, float]:
    """Adds one rental to the customer's score this week. Returns the key and the new score."""
    key = leaderboard_key()
    pipe = r.pipeline()  # MULTI/EXEC: the two commands run together, nothing in between
    pipe.zincrby(key, 1, f"customer:{customer_id}")
    # NX: only set the expiry if the key has none, which is on the first write of the week.
    pipe.expire(key, LEADERBOARD_TTL, nx=True)
    score, _ = pipe.execute()
    return key, score
