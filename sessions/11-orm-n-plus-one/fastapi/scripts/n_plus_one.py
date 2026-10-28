"""The tutorial script: the same listing with lazy and eager loading, then the aggregation.

Run with: uv run python -m scripts.n_plus_one
Set SQL_ECHO=false in .env to see only the counts.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import count_queries, engine
from app.models import Customer, Rental


def lazy() -> int:
    # N+1: one query for customers, then one per customer.
    with Session(engine) as session, count_queries() as statements:
        customers = session.scalars(select(Customer).order_by(Customer.customer_id).limit(20)).all()
        for c in customers:
            print(c.first_name, len(c.rentals))
    return len(statements)


def eager() -> int:
    # A new session, so no rentals are already loaded from the block above.
    with Session(engine) as session, count_queries() as statements:
        stmt = select(Customer).options(selectinload(Customer.rentals)).order_by(Customer.customer_id).limit(20)
        for c in session.scalars(stmt):
            print(c.first_name, len(c.rentals))
    return len(statements)


def top5() -> int:
    with Session(engine) as session, count_queries() as statements:
        stmt = (
            select(Customer.last_name, func.count(Rental.rental_id).label("n"))
            .join(Customer.rentals)
            .group_by(Customer.customer_id)
            .order_by(func.count(Rental.rental_id).desc())
            .limit(5)
        )
        for row in session.execute(stmt):
            print(row.last_name, row.n)
    return len(statements)


if __name__ == "__main__":
    results = {"lazy (N+1)": lazy(), "selectinload": eager(), "top 5 aggregation": top5()}
    print()
    for name, n in results.items():
        print(f"{name:20} {n:3} queries")
