from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Path, Response
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.db import get_session, mongo_db, r
from app.films_sets import films_key, postgres_film_count
from app.models import Account, Inventory, Rental

app = FastAPI(title="Session 17: three engines, one API")

MONTH = Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2022-07"])


class Amount(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class Balance(BaseModel):
    balance: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class NewRental(BaseModel):
    customer_id: int
    inventory_id: int
    staff_id: int = 1


@app.get("/health")
def health(response: Response, session: Session = Depends(get_session)):
    result = {}
    for name, ping in {
        "postgres": lambda: session.execute(text("SELECT 1")),
        "mongo": lambda: mongo_db.command("ping"),
        "redis": r.ping,
    }.items():
        try:
            ping()
            result[name] = "ok"
        except Exception as exc:  # report every engine, even when one is down
            result[name] = f"error: {exc}"
    if any(v != "ok" for v in result.values()):
        response.status_code = 503
    return result


# --- PostgreSQL: account withdrawals (session 08) -----------------------------

@app.put("/accounts/{account_id}")
def set_account(account_id: int, body: Balance, session: Session = Depends(get_session)):
    """Creates the account or resets its balance. Used by the tests to start from a known state."""
    with session.begin():
        session.merge(Account(id=account_id, balance=body.balance))
    return {"id": account_id, "balance": str(body.balance)}


@app.get("/accounts/{account_id}")
def get_account(account_id: int, session: Session = Depends(get_session)):
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(404, "Account not found")
    return {"id": account.id, "balance": str(account.balance)}


@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: int, body: Amount, session: Session = Depends(get_session)):
    # Read and write in one statement: concurrent withdrawals cannot both see the old balance.
    with session.begin():
        new_balance = session.execute(
            update(Account)
            .where(Account.id == account_id, Account.balance >= body.amount)
            .values(balance=Account.balance - body.amount)
            .returning(Account.balance)
        ).scalar_one_or_none()
        if new_balance is None:
            if session.get(Account, account_id) is None:
                raise HTTPException(404, "Account not found")
            raise HTTPException(409, "Insufficient balance")
    return {"id": account_id, "balance": str(new_balance)}


# --- PostgreSQL + Redis: rentals keep the derived set up to date (session 16) ---

@app.post("/rentals", status_code=201)
def create_rental(body: NewRental, session: Session = Depends(get_session)):
    with session.begin():
        film_id = session.scalar(select(Inventory.film_id).where(Inventory.inventory_id == body.inventory_id))
        if film_id is None:
            raise HTTPException(404, "Inventory item not found")
        rental = Rental(customer_id=body.customer_id, inventory_id=body.inventory_id, staff_id=body.staff_id)
        session.add(rental)
        session.flush()
        rental_id = rental.rental_id
    # Source of truth first (committed above), then the derived copy. If this line
    # fails, PostgreSQL is still right and the rebuild script repairs Redis.
    r.sadd(films_key(body.customer_id), film_id)
    return {"rental_id": rental_id, "customer_id": body.customer_id, "film_id": film_id}


@app.get("/customers/{customer_id}/films")
def customer_films(customer_id: int, session: Session = Depends(get_session)):
    """Both copies side by side, so a test or a person can compare them."""
    return {
        "customer_id": customer_id,
        "redis": r.scard(films_key(customer_id)),
        "postgres": postgres_film_count(session, customer_id),
    }


# --- PostgreSQL -> MongoDB: frozen monthly report (session 14) ------------------

@app.post("/reports/monthly/{month}", status_code=201)
def create_monthly_report(month: str = MONTH, session: Session = Depends(get_session)):
    start = date.fromisoformat(f"{month}-01")
    rows = session.execute(
        text("""
            SELECT st.store_id, count(*) AS payments, sum(p.amount) AS revenue
            FROM payment p
            JOIN staff st ON st.staff_id = p.staff_id
            WHERE p.payment_date >= :start AND p.payment_date < :start + interval '1 month'
            GROUP BY st.store_id
            ORDER BY st.store_id
        """),
        {"start": start},
    ).all()
    report = {
        "_id": month,
        "generated_at": datetime.now(UTC),
        "stores": [{"store_id": s, "payments": n, "revenue": str(rev)} for s, n, rev in rows],
    }
    try:
        mongo_db.monthly_reports.insert_one(report)
    except DuplicateKeyError:
        raise HTTPException(409, f"Report {month} already exists and is frozen")
    return {"_id": month, "stores": len(rows)}


@app.get("/reports/monthly/{month}")
def read_monthly_report(month: str = MONTH):
    report = mongo_db.monthly_reports.find_one({"_id": month})
    if report is None:
        raise HTTPException(404, f"No report for {month}")
    return report
