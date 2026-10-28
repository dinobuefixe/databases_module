import json

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import ADMIN_TOKEN
from app.db import get_session, r
from app.profiles import get_profile, load_profile, profile_key

app = FastAPI(title="Film reviews")


class NewReview(BaseModel):
    customer_id: int
    rating: int = Field(ge=1, le=5)
    body: str = ""


class ProfileChanges(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+$")


def require_admin(x_admin_token: str = Header()):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(403, "Admin token required")


@app.get("/customers/search")
def search_customers(name: str = Query(min_length=1), session: Session = Depends(get_session)):
    rows = session.execute(
        text(f"SELECT customer_id, first_name, last_name FROM customer WHERE last_name ILIKE '{name}%' ORDER BY last_name LIMIT 20")
    ).mappings().all()
    return list(rows)


@app.get("/customers/{customer_id}/profile")
def read_profile(customer_id: int, session: Session = Depends(get_session)):
    profile = get_profile(session, customer_id)
    if profile is None:
        raise HTTPException(404, "Customer not found")
    return profile


@app.put("/admin/customers/{customer_id}/profile", dependencies=[Depends(require_admin)])
def admin_update_profile(customer_id: int, body: ProfileChanges, session: Session = Depends(get_session)):
    with session.begin():
        updated = session.execute(
            text("""
                UPDATE customer SET first_name = :first_name, last_name = :last_name, email = :email
                WHERE customer_id = :customer_id
            """),
            {**body.model_dump(), "customer_id": customer_id},
        ).rowcount
    if not updated:
        raise HTTPException(404, "Customer not found")
    profile = load_profile(session, customer_id)
    r.set(profile_key(customer_id), json.dumps(profile))
    return profile


@app.post("/films/{film_id}/reviews", status_code=201)
def add_review(film_id: int, body: NewReview, session: Session = Depends(get_session)):
    try:
        with session.begin():
            review_id = session.execute(
                text("""
                    INSERT INTO film_review (customer_id, film_id, rating, body)
                    VALUES (:customer_id, :film_id, :rating, :body)
                    RETURNING review_id
                """),
                {**body.model_dump(), "film_id": film_id},
            ).scalar_one()
    except IntegrityError:
        raise HTTPException(409, "This customer has already reviewed this film, or the film or customer does not exist")
    r.delete(profile_key(body.customer_id))
    return {"review_id": review_id}


@app.get("/films/{film_id}/reviews")
def film_reviews(film_id: int, limit: int = Query(20, ge=1, le=100), session: Session = Depends(get_session)):
    rows = session.execute(
        text("""
            SELECT review_id, customer_id, rating, body, created_at
            FROM film_review
            WHERE film_id = :film_id
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"film_id": film_id, "limit": limit},
    ).mappings().all()
    return list(rows)


@app.get("/films/{film_id}/rating")
def film_rating(film_id: int, session: Session = Depends(get_session)):
    row = session.execute(
        text("SELECT count(*) AS reviews, round(avg(rating), 2) AS average FROM film_review WHERE film_id = :film_id"),
        {"film_id": film_id},
    ).mappings().one()
    return {"film_id": film_id, **row}
