"""Three ways to withdraw money from an account. Only two of them are safe under concurrency."""

import time
from decimal import Decimal

from app.db import SQL_DIR, pg_connect

# Pause between the read and the write in the naive version. It does not cause the bug,
# it only widens the window so the lost update shows up every time instead of now and then.
NAIVE_PAUSE_SECONDS = 0.05


class AccountNotFound(Exception):
    pass


def create_table() -> None:
    with pg_connect() as conn:
        conn.execute((SQL_DIR / "001_account.sql").read_text())


def reset(balance: Decimal = Decimal(100)) -> list[dict]:
    """Accounts 1 and 2 back to the same balance."""
    with pg_connect() as conn:
        return conn.execute(
            """
            INSERT INTO account (id, balance) VALUES (1, %(b)s), (2, %(b)s)
            ON CONFLICT (id) DO UPDATE SET balance = EXCLUDED.balance
            RETURNING *
            """,
            {"b": balance},
        ).fetchall()


def get_balance(account_id: int) -> Decimal:
    with pg_connect() as conn:
        row = conn.execute("SELECT balance FROM account WHERE id = %s", (account_id,)).fetchone()
    if row is None:
        raise AccountNotFound(account_id)
    return row["balance"]


def withdraw_naive(account_id: int, amount: Decimal) -> bool:
    """Read, compute in Python, write. Two requests can read the same balance: lost update."""
    with pg_connect() as conn:
        row = conn.execute("SELECT balance FROM account WHERE id = %s", (account_id,)).fetchone()
        if row is None:
            raise AccountNotFound(account_id)
        if row["balance"] < amount:
            return False
        time.sleep(NAIVE_PAUSE_SECONDS)
        # Another transaction may have changed the balance since we read it. We overwrite it anyway.
        conn.execute("UPDATE account SET balance = %s WHERE id = %s", (row["balance"] - amount, account_id))
        return True


def withdraw_atomic(account_id: int, amount: Decimal) -> bool:
    """Fix 1: read and write in one statement. The row count says whether it happened."""
    with pg_connect() as conn:
        cur = conn.execute(
            "UPDATE account SET balance = balance - %s WHERE id = %s AND balance >= %s",
            (amount, account_id, amount),
        )
        if cur.rowcount == 1:
            return True
        if conn.execute("SELECT 1 FROM account WHERE id = %s", (account_id,)).fetchone() is None:
            raise AccountNotFound(account_id)
        return False


def withdraw_lock(account_id: int, amount: Decimal) -> bool:
    """Fix 2: SELECT ... FOR UPDATE. Other transactions wait at the SELECT until this one commits."""
    with pg_connect() as conn:
        row = conn.execute(
            "SELECT balance FROM account WHERE id = %s FOR UPDATE", (account_id,)
        ).fetchone()
        if row is None:
            raise AccountNotFound(account_id)
        if row["balance"] < amount:
            return False
        # Same read-compute-write as the naive version, but nobody can change the row in between.
        conn.execute("UPDATE account SET balance = %s WHERE id = %s", (row["balance"] - amount, account_id))
        # Leaving the `with` block commits and releases the lock.
        return True


STRATEGIES = {"naive": withdraw_naive, "atomic": withdraw_atomic, "lock": withdraw_lock}
