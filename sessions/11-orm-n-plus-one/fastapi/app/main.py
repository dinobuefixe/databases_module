from fastapi import Depends, FastAPI, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import count_queries, get_session
from app.models import Customer, Rental

app = FastAPI(title="Session 11: ORM and the N+1 problem")


@app.get("/customers")
def list_customers(
    limit: int = Query(20, ge=1, le=500),
    eager: bool = False,
    session: Session = Depends(get_session),
):
    """Customers with their rental count, and how many SQL queries it took."""
    with count_queries() as statements:
        stmt = select(Customer).order_by(Customer.customer_id).limit(limit)
        if eager:
            # Fixed: a second query with WHERE customer_id IN (...) loads every rental at once.
            stmt = stmt.options(selectinload(Customer.rentals))
        customers = session.scalars(stmt).all()
        # Without eager loading, each len(c.rentals) runs its own SELECT: 1 + N queries.
        rows = [
            {"customer_id": c.customer_id, "name": f"{c.first_name} {c.last_name}", "rentals": len(c.rentals)}
            for c in customers
        ]
    return {"eager": eager, "queries": len(statements), "customers": rows}


@app.get("/customers/top")
def top_customers(limit: int = Query(5, ge=1, le=100), session: Session = Depends(get_session)):
    """Aggregation in the database: one query, no Rental objects loaded into Python."""
    n = func.count(Rental.rental_id).label("n")
    stmt = (
        select(Customer.customer_id, Customer.first_name, Customer.last_name, n)
        .join(Customer.rentals)
        .group_by(Customer.customer_id)
        .order_by(n.desc(), Customer.customer_id)
        .limit(limit)
    )
    with count_queries() as statements:
        rows = [row._asdict() for row in session.execute(stmt)]
    return {"queries": len(statements), "sql": str(stmt), "customers": rows}


@app.get("/rentals/recent")
def recent_rentals(
    limit: int = Query(10, ge=1, le=500),
    eager: bool = False,
    session: Session = Depends(get_session),
):
    """The N:1 direction: each rental and its customer's name."""
    with count_queries() as statements:
        stmt = select(Rental).order_by(Rental.rental_date.desc(), Rental.rental_id).limit(limit)
        if eager:
            # One customer per rental: a JOIN in the same query is enough.
            stmt = stmt.options(joinedload(Rental.customer))
        rentals = session.scalars(stmt).all()
        rows = [
            {
                "rental_id": r.rental_id,
                "rental_date": r.rental_date,
                "customer": f"{r.customer.first_name} {r.customer.last_name}",
            }
            for r in rentals
        ]
    return {"eager": eager, "queries": len(statements), "rentals": rows}
