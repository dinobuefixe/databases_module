"""The tutorial's concurrency test, run against the database through app/accounts.py.

    uv run pytest -v
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app.accounts import STRATEGIES, create_table, get_balance, reset

REQUESTS = 50
WORKERS = 20  # parallel connections; the tutorial uses 50, kept lower for a shared server


def fire(strategy: str) -> int:
    withdraw = STRATEGIES[strategy]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(lambda _: withdraw(1, Decimal(10)), range(REQUESTS)))
    return sum(results)


@pytest.fixture(autouse=True)
def account_with_100():
    create_table()
    reset(Decimal(100))  # account 1 starts with a balance of 100


@pytest.mark.parametrize("strategy", ["atomic", "lock"])
def test_exactly_ten_withdrawals_succeed(strategy):
    succeeded = fire(strategy)
    assert succeeded == 10, f"{succeeded} withdrawals succeeded"
    assert get_balance(1) == 0


@pytest.mark.xfail(reason="read-then-write without a lock loses updates", strict=True)
def test_naive_read_then_write():
    succeeded = fire("naive")
    assert succeeded == 10 and get_balance(1) == 0, f"{succeeded} succeeded, balance {get_balance(1)}"
