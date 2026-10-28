import time
from decimal import Decimal
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.db import get_session, r
from app.films_sets import verify_all
from app.models import Account

app = FastAPI(title="Session 19: delivery demo")


class Amount(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class Balance(BaseModel):
    balance: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


@app.get("/health")
def health(response: Response, session: Session = Depends(get_session)):
    result = {}
    for name, ping in {"postgres": lambda: session.execute(text("SELECT 1")), "redis": r.ping}.items():
        try:
            ping()
            result[name] = "ok"
        except Exception as exc:  # report every engine, even when one is down
            result[name] = f"error: {exc}"
    if any(v != "ok" for v in result.values()):
        response.status_code = 503
    return result


@app.put("/accounts/{account_id}")
def set_account(account_id: int, body: Balance, session: Session = Depends(get_session)):
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
def withdraw(
    account_id: int,
    body: Amount,
    strategy: Literal["naive", "atomic"] = "atomic",
    session: Session = Depends(get_session),
):
    with session.begin():
        if strategy == "naive":
            # Read, compute in Python, write: the lost update from session 08.
            account = session.scalar(select(Account).where(Account.id == account_id))
            if account is None:
                raise HTTPException(404, "Account not found")
            if account.balance < body.amount:
                raise HTTPException(409, "Insufficient balance")
            time.sleep(0.01)  # stands for any work between the read and the write
            account.balance = account.balance - body.amount
            new_balance = account.balance
        else:
            # One statement reads and writes: concurrent requests queue on the row.
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
    return {"id": account_id, "balance": str(new_balance), "strategy": strategy}


@app.get("/verify")
def verify(response: Response, session: Session = Depends(get_session)):
    mismatches = verify_all(session)
    if mismatches:
        response.status_code = 409
    return {"ok": not mismatches, "mismatches": len(mismatches)}
