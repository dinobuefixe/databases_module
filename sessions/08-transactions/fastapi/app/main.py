from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.accounts import STRATEGIES, AccountNotFound, create_table, get_balance, reset


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield


app = FastAPI(title="Session 08: transactions and concurrency", lifespan=lifespan)


class Withdrawal(BaseModel):
    amount: Decimal = Field(gt=0)


@app.post("/accounts/reset")
def reset_accounts(balance: Decimal = Query(Decimal(100), ge=0)):
    """Accounts 1 and 2 back to `balance` (100 by default)."""
    return reset(balance)


@app.get("/accounts/{account_id}")
def read_account(account_id: int):
    try:
        return {"id": account_id, "balance": get_balance(account_id)}
    except AccountNotFound:
        raise HTTPException(404, "account not found")


@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: int, body: Withdrawal, strategy: Literal["naive", "atomic", "lock"] = "atomic"):
    """Withdraw `amount`. 200 if it happened, 409 if the balance was too low."""
    # A sync endpoint: FastAPI runs it in a thread pool, so requests really run at the same time.
    try:
        ok = STRATEGIES[strategy](account_id, body.amount)
    except AccountNotFound:
        raise HTTPException(404, "account not found")
    if not ok:
        raise HTTPException(409, "insufficient balance")
    return {"withdrawn": body.amount, "strategy": strategy}
