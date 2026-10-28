import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import PROFILE_TTL
from app.db import r

PROFILE_SQL = text("""
    SELECT c.customer_id, c.first_name, c.last_name, c.email,
           (SELECT count(*) FROM film_review fr WHERE fr.customer_id = c.customer_id) AS reviews
    FROM customer c
    WHERE c.customer_id = :customer_id
""")


def profile_key(customer_id: int) -> str:
    return f"profile:{customer_id}"


def load_profile(session: Session, customer_id: int) -> dict | None:
    row = session.execute(PROFILE_SQL, {"customer_id": customer_id}).mappings().one_or_none()
    return dict(row) if row else None


def get_profile(session: Session, customer_id: int) -> dict | None:
    cached = r.get(profile_key(customer_id))
    if cached is not None:
        return json.loads(cached)
    profile = load_profile(session, customer_id)
    if profile is not None:
        r.set(profile_key(customer_id), json.dumps(profile), ex=PROFILE_TTL)
    return profile
