"""Two transfers in opposite directions, at the same time.

Part 1: each transaction locks its source row first, then the destination row.
A holds row 1 and waits for row 2; B holds row 2 and waits for row 1. PostgreSQL detects the
cycle after deadlock_timeout (1 s by default) and aborts one of them. We catch it and retry.

Part 2: both lock the two rows in the same order (ascending id). B waits for A; no deadlock.
"""

import threading
import time

import psycopg

from app.accounts import create_table, reset
from app.db import pg_connect


def transfer_unordered(name: str, source: int, target: int, barrier: threading.Barrier) -> None:
    with pg_connect() as conn:
        conn.execute("SELECT balance FROM account WHERE id = %s FOR UPDATE", (source,))
        print(f"{name}: locked row {source}")
        barrier.wait()  # both threads now hold their first lock
        print(f"{name}: waiting for row {target}")
        conn.execute("SELECT balance FROM account WHERE id = %s FOR UPDATE", (target,))
        move(conn, source, target)
    print(f"{name}: committed")


def transfer_ordered(name: str, source: int, target: int, barrier: threading.Barrier) -> None:
    barrier.wait()  # start together
    with pg_connect() as conn:
        print(f"{name}: asking for rows 1 and 2")
        # One statement locks both rows, always in ascending id order.
        conn.execute(
            "SELECT id FROM account WHERE id IN (%s, %s) ORDER BY id FOR UPDATE", (source, target)
        )
        print(f"{name}: locked rows 1 and 2")
        time.sleep(0.2)  # hold the locks a moment so the other thread has to wait
        move(conn, source, target)
    print(f"{name}: committed")


def move(conn: psycopg.Connection, source: int, target: int, amount: int = 10) -> None:
    conn.execute("UPDATE account SET balance = balance - %s WHERE id = %s", (amount, source))
    conn.execute("UPDATE account SET balance = balance + %s WHERE id = %s", (amount, target))


def with_retry(fn, name: str, *args) -> None:
    try:
        fn(name, *args)
    except psycopg.errors.DeadlockDetected as exc:
        print(f"\n{name}: ERROR: {exc.diag.message_primary}")
        print(f"DETAIL: {exc.diag.message_detail}")
        print(f"HINT: {exc.diag.message_hint}\n")
        print(f"{name}: rolled back by PostgreSQL, retrying")
        # The other transaction has the locks now; the retry waits for it and then succeeds.
        fn(name, *args[:-1], threading.Barrier(1))


def run(title: str, fn) -> None:
    print(f"\n=== {title}")
    reset()
    barrier = threading.Barrier(2)
    a = threading.Thread(target=with_retry, args=(fn, "A", 1, 2, barrier))
    b = threading.Thread(target=with_retry, args=(fn, "B", 2, 1, barrier))
    a.start(); b.start(); a.join(); b.join()
    with pg_connect() as conn:
        rows = conn.execute("SELECT id, balance FROM account WHERE id IN (1, 2) ORDER BY id").fetchall()
    print("balances:", {r["id"]: float(r["balance"]) for r in rows}, "(10 moved each way, so both end at 100)")


def main() -> None:
    create_table()
    run("Part 1: locks taken in opposite order", transfer_unordered)
    run("Part 2: locks taken in a fixed order", transfer_ordered)


if __name__ == "__main__":
    main()
