"""Reproduce tasks 1-3 of the session 08 exercise on ex08.

Run with:
    uv run python reproduce.py

It uses two separate connections (like two psql sessions) and drives the
interleavings explicitly. The balance of customer 1 is reset to 100 before
each task.
"""

from __future__ import annotations

import os
import threading

import psycopg

DSN = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:change-me-postgres@localhost:5432/ex08"
)


def connect() -> psycopg.Connection:
    # autocommit=True so BEGIN/COMMIT/ROLLBACK are sent literally, exactly as
    # the two-session tables in the exercise show them.
    return psycopg.connect(DSN, autocommit=True)


def reset(conn: psycopg.Connection) -> None:
    conn.execute("UPDATE customer SET balance = 100 WHERE customer_id = 1")


def balance(conn: psycopg.Connection) -> str:
    return str(conn.execute(
        "SELECT balance FROM customer WHERE customer_id = 1"
    ).fetchone()[0])


def task1_lost_update() -> None:
    print("=" * 70)
    print("Task 1 - lost update (expect final balance 90, should be 80)")
    print("=" * 70)
    a, b = connect(), connect()
    reset(a)
    print("initial balance:", balance(a))

    a.execute("BEGIN")
    print("A  BEGIN;  SELECT balance ->", a.execute(
        "SELECT balance FROM customer WHERE customer_id = 1").fetchone()[0])

    b.execute("BEGIN")
    print("B          BEGIN;  SELECT balance ->", b.execute(
        "SELECT balance FROM customer WHERE customer_id = 1").fetchone()[0])

    a.execute("UPDATE customer SET balance = 90 WHERE customer_id = 1")
    print("A  UPDATE balance = 90;")
    a.execute("COMMIT")
    print("A  COMMIT;")

    b.execute("UPDATE customer SET balance = 90 WHERE customer_id = 1")
    print("B          UPDATE balance = 90;")
    b.execute("COMMIT")
    print("B          COMMIT;")

    print("final balance:", balance(a), "(lost update: one -10 disappeared)")
    a.close()
    b.close()


def task2_atomic() -> None:
    print()
    print("=" * 70)
    print("Task 2a - fix with an atomic UPDATE (expect final balance 80)")
    print("=" * 70)
    a, b = connect(), connect()
    reset(a)
    print("initial balance:", balance(a))

    a.execute("BEGIN")
    a.execute("UPDATE customer SET balance = balance - 10 "
              "WHERE customer_id = 1 AND balance >= 10")
    print("A  BEGIN; UPDATE balance = balance - 10 ... (lock held)")

    b.execute("BEGIN")
    print("B          BEGIN; UPDATE balance = balance - 10 ... (waits for A)")
    blocked = threading.Thread(
        target=lambda: b.execute(
            "UPDATE customer SET balance = balance - 10 "
            "WHERE customer_id = 1 AND balance >= 10"
        )
    )
    blocked.start()
    blocked.join(timeout=2)
    print("B          still waiting:", blocked.is_alive())

    a.execute("COMMIT")
    print("A  COMMIT;")
    blocked.join()
    print("B          UPDATE completed")
    b.execute("COMMIT")
    print("B          COMMIT;")

    print("final balance:", balance(a))
    a.close()
    b.close()


def task2_for_update() -> None:
    print()
    print("=" * 70)
    print("Task 2b - fix with SELECT ... FOR UPDATE (expect final balance 80)")
    print("=" * 70)
    a, b = connect(), connect()
    reset(a)
    print("initial balance:", balance(a))

    a.execute("BEGIN")
    va = a.execute("SELECT balance FROM customer WHERE customer_id = 1 "
                   "FOR UPDATE").fetchone()[0]
    print("A  BEGIN; SELECT ... FOR UPDATE ->", va)

    b.execute("BEGIN")
    got: list = []

    def read_for_update():
        got.append(b.execute(
            "SELECT balance FROM customer WHERE customer_id = 1 FOR UPDATE"
        ).fetchone()[0])

    t = threading.Thread(target=read_for_update)
    t.start()
    t.join(timeout=2)
    print("B          BEGIN; SELECT ... FOR UPDATE (waits for A)")

    a.execute("UPDATE customer SET balance = %s WHERE customer_id = 1", (va - 10,))
    print("A  UPDATE balance =", va - 10)
    a.execute("COMMIT")
    print("A  COMMIT;")

    t.join()
    print("B          SELECT ... FOR UPDATE ->", got[0], "(read after A committed)")
    b.execute("UPDATE customer SET balance = %s WHERE customer_id = 1", (got[0] - 10,))
    print("B          UPDATE balance =", got[0] - 10)
    b.execute("COMMIT")
    print("B          COMMIT;")

    print("final balance:", balance(a))
    a.close()
    b.close()


def task3_deadlock() -> None:
    print()
    print("=" * 70)
    print("Task 3 - deadlock")
    print("=" * 70)
    a, b = connect(), connect()
    a.execute("UPDATE customer SET balance = 100")
    a_locked = threading.Event()
    b_locked = threading.Event()
    errors: dict[str, psycopg.Error] = {}

    def session_a() -> None:
        try:
            a.execute("BEGIN")
            a.execute("UPDATE customer SET balance = balance - 1 WHERE customer_id = 1")
            print("A  BEGIN; UPDATE customer 1;")
            a_locked.set()
            b_locked.wait()
            print("A  UPDATE customer 2;  (waits for B)")
            a.execute("UPDATE customer SET balance = balance - 1 WHERE customer_id = 2")
            print("A  UPDATE customer 2;  (done)")
            a.execute("COMMIT")
        except psycopg.Error as exc:
            errors["A"] = exc

    def session_b() -> None:
        try:
            b.execute("BEGIN")
            a_locked.wait()
            b.execute("UPDATE customer SET balance = balance - 1 WHERE customer_id = 2")
            print("B          BEGIN; UPDATE customer 2;")
            b_locked.set()
            print("B          UPDATE customer 1;  (waits for A)")
            b.execute("UPDATE customer SET balance = balance - 1 WHERE customer_id = 1")
            print("B          UPDATE customer 1;  (done)")
            b.execute("COMMIT")
        except psycopg.Error as exc:
            errors["B"] = exc

    ta = threading.Thread(target=session_a)
    tb = threading.Thread(target=session_b)
    ta.start()
    tb.start()
    ta.join()
    tb.join()

    for who, exc in errors.items():
        diag = exc.diag
        print()
        print(f"--- session {who} aborted ---")
        print("SQLSTATE:", diag.sqlstate)
        print("ERROR: ", diag.message_primary)
        if diag.message_detail:
            for line in diag.message_detail.splitlines():
                print("DETAIL:", line)
        if diag.message_hint:
            print("HINT:  ", diag.message_hint)
        if diag.context:
            print("CONTEXT:", diag.context)

    print()
    print("customer 1 balance:", balance(a), " customer 2 balance:", balance(a))
    a.close()
    b.close()


if __name__ == "__main__":
    task1_lost_update()
    task2_atomic()
    task2_for_update()
    task3_deadlock()
