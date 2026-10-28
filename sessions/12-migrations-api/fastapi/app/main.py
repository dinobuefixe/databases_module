from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Customer

app = FastAPI(title="Session 12: migrations and a transactional API")


class Amount(BaseModel):
    # Pydantic rejects 0, negative values and more than 2 decimal places with a 422
    # before the endpoint runs.
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


def as_dict(c: Customer) -> dict:
    return {
        "customer_id": c.customer_id,
        "name": f"{c.first_name} {c.last_name}",
        "tier": c.tier,
        "balance": str(c.balance),  # a string keeps the exact decimal value in JSON
    }


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int, session: Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(404, "Customer not found")
    return as_dict(customer)


@app.post("/customers/{customer_id}/top-up")
def top_up(customer_id: int, body: Amount, session: Session = Depends(get_session)):
    """Adds credit so the charge endpoint has something to take."""
    with session.begin():
        customer = session.scalars(
            select(Customer).where(Customer.customer_id == customer_id).with_for_update()
        ).one_or_none()
        if customer is None:
            raise HTTPException(404, "Customer not found")
        customer.balance += body.amount
        result = as_dict(customer)
    return result


@app.post("/customers/{customer_id}/charge")
def charge(customer_id: int, body: Amount, session: Session = Depends(get_session)):
    # session.begin() commits at the end of the block, or rolls back if an
    # exception (including HTTPException) leaves it.
    with session.begin():
        # SELECT ... FOR UPDATE: a second charge for the same customer waits here
        # until this transaction ends, then reads the new balance.
        customer = session.scalars(
            select(Customer).where(Customer.customer_id == customer_id).with_for_update()
        ).one_or_none()
        if customer is None:
            raise HTTPException(404, "Customer not found")
        if customer.balance < body.amount:
            raise HTTPException(409, "Insufficient balance")
        customer.balance -= body.amount
        result = as_dict(customer)
    return result
