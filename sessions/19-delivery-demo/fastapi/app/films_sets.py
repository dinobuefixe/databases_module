"""customer:{id}:films in Redis, derived from rentals in PostgreSQL (session 16)."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import r


def films_key(customer_id: int) -> str:
    return f"customer:{customer_id}:films"


def rebuild_all(session: Session) -> int:
    rows = session.execute(text("""
        SELECT c.customer_id,
               array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL)
        FROM customer c
        LEFT JOIN rental r    ON r.customer_id = c.customer_id
        LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
        GROUP BY c.customer_id
    """)).all()
    pipe = r.pipeline(transaction=False)
    for customer_id, film_ids in rows:
        key, tmp = films_key(customer_id), films_key(customer_id) + ":rebuild"
        pipe.delete(tmp)
        if film_ids:
            pipe.sadd(tmp, *film_ids)
            pipe.rename(tmp, key)
        else:
            pipe.delete(key)
    pipe.execute()
    return len(rows)


def verify_all(session: Session) -> list[dict]:
    rows = session.execute(text("""
        SELECT r.customer_id, count(DISTINCT i.film_id)
        FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
        GROUP BY r.customer_id
        ORDER BY r.customer_id
    """)).all()
    pipe = r.pipeline(transaction=False)
    for customer_id, _ in rows:
        pipe.scard(films_key(customer_id))
    return [
        {"customer_id": customer_id, "redis": actual, "postgres": expected}
        for (customer_id, expected), actual in zip(rows, pipe.execute())
        if actual != expected
    ]
