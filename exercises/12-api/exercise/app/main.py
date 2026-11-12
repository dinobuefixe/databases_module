"""Transactional rental API for the session 12 exercise.

Run with:
    uv run uvicorn app.main:app --port 8000

Every request gets its own ``Session``. ``POST /rentals`` runs in a single
transaction, locks a free copy with ``FOR UPDATE SKIP LOCKED`` and retries the
whole transaction if the partial unique index rejects the insert.

Set ``SQL_ECHO=1`` to log every statement (used to count the queries of
``GET /rentals/overdue``).
"""

from __future__ import annotations

import os
from datetime import date, datetime, time, timezone

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from models import Customer, Film, Inventory, Rental, Staff, make_engine

engine = make_engine(echo=os.environ.get("SQL_ECHO") == "1")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

app = FastAPI(title="ex12 rentals API")

MAX_RETRIES = 3


def get_session():
    with SessionLocal() as session:
        yield session


class RentalIn(BaseModel):
    customer_id: int
    film_id: int
    store_id: int
    staff_id: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _rent_one(body: RentalIn) -> tuple[int, int]:
    """Try once to insert a rental. Raises IntegrityError on the unique index."""
    with SessionLocal() as session:
        with session.begin():
            if session.get(Customer, body.customer_id) is None:
                raise HTTPException(404, "Customer not found")
            if session.get(Film, body.film_id) is None:
                raise HTTPException(404, "Film not found")
            if session.get(Staff, body.staff_id) is None:
                raise HTTPException(404, "Staff not found")

            inventory_id = session.scalars(
                select(Inventory.inventory_id)
                .where(
                    Inventory.film_id == body.film_id,
                    Inventory.store_id == body.store_id,
                    ~Inventory.rentals.any(Rental.return_date.is_(None)),
                )
                .order_by(Inventory.inventory_id)
                .with_for_update(skip_locked=True)
                .limit(1)
            ).first()

            if inventory_id is None:
                raise HTTPException(409, "No copy available")

            rental = Rental(
                rental_date=_now(),
                inventory_id=inventory_id,
                customer_id=body.customer_id,
                staff_id=body.staff_id,
            )
            session.add(rental)
            session.flush()
            return rental.rental_id, inventory_id


@app.post("/rentals", status_code=201)
def create_rental(body: RentalIn) -> dict:
    """Rent a free copy of a film, retrying on the one-open-rental index."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            rental_id, inventory_id = _rent_one(body)
            return {"rental_id": rental_id, "inventory_id": inventory_id}
        except IntegrityError:
            # Another request rented the copy between our SELECT and INSERT.
            # The transaction was rolled back; start a new one.
            if attempt == MAX_RETRIES:
                raise HTTPException(409, "No copy available") from None
    raise HTTPException(409, "No copy available")


@app.post("/rentals/{rental_id}/return")
def return_rental(rental_id: int) -> dict:
    with SessionLocal() as session:
        with session.begin():
            rental = session.get(Rental, rental_id, with_for_update=True)
            if rental is None:
                raise HTTPException(404, "Rental not found")
            if rental.return_date is not None:
                raise HTTPException(409, "Rental already returned")
            rental.return_date = _now()
        return {
            "rental_id": rental.rental_id,
            "return_date": rental.return_date,
        }


@app.get("/rentals/overdue")
def overdue(as_of: date = date(2026, 7, 31), session: Session = Depends(get_session)) -> dict:
    """Open rentals whose due date is before ``as_of``, in a single query."""
    as_of_dt = datetime.combine(as_of, time.min, tzinfo=timezone.utc)
    due_date = Rental.rental_date + (
        Film.rental_duration * text("interval '1 day'")
    )

    stmt = (
        select(
            Rental.rental_id,
            Rental.rental_date,
            due_date.label("due_date"),
            Customer.customer_id,
            Customer.first_name,
            Customer.last_name,
            Film.film_id,
            Film.title,
        )
        .join(Inventory, Rental.inventory_id == Inventory.inventory_id)
        .join(Film, Inventory.film_id == Film.film_id)
        .join(Customer, Rental.customer_id == Customer.customer_id)
        .where(Rental.return_date.is_(None), due_date < as_of_dt)
        .order_by(Rental.rental_date, Rental.rental_id)
    )

    items = [
        {
            "rental_id": row.rental_id,
            "rental_date": row.rental_date,
            "due_date": row.due_date,
            "customer": {
                "customer_id": row.customer_id,
                "first_name": row.first_name,
                "last_name": row.last_name,
            },
            "film": {"film_id": row.film_id, "title": row.title},
        }
        for row in session.execute(stmt)
    ]
    return {"count": len(items), "items": items}
