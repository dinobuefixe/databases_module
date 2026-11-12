"""Task 4 - write skew on the rule "every store keeps at least one active staff".

Run with:
    uv run python write_skew.py

It starts one thread per active staff member of store 1 (20 of them), each with
its own connection. Every thread runs one transaction: count the active staff of
store 1, and if the count is above 1 set its own member to ``active = false``.
A ``threading.Barrier(20)`` between the count and the update makes every thread
read before any thread writes.

Under READ COMMITTED all 20 threads read count = 20, so all 20 go off call and
the store is left with 0 active members. Under SERIALIZABLE the read-write
conflict is detected, conflicting transactions are retried from the start
(without the barrier) and exactly 1 member stays active.
"""

from __future__ import annotations

import os
import threading
from collections import Counter

import psycopg
from psycopg import IsolationLevel

DSN = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:change-me-postgres@localhost:5432/ex08"
)
N = 20


def connect(isolation: IsolationLevel) -> psycopg.Connection:
    conn = psycopg.connect(DSN)
    conn.isolation_level = isolation
    return conn


def active_staff_ids(conn: psycopg.Connection) -> list[int]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT staff_id FROM staff WHERE store_id = 1 AND active ORDER BY staff_id"
        )
    ]


def active_count(conn: psycopg.Connection) -> int:
    return conn.execute(
        "SELECT count(*) FROM staff WHERE store_id = 1 AND active"
    ).fetchone()[0]


def reset(conn: psycopg.Connection) -> None:
    conn.execute("UPDATE staff SET active = true WHERE store_id = 1")


def run(isolation: IsolationLevel) -> tuple[int, Counter]:
    setup = connect(IsolationLevel.READ_COMMITTED)
    reset(setup)
    staff_ids = active_staff_ids(setup)
    setup.commit()
    assert len(staff_ids) == N, f"expected {N} active staff, got {len(staff_ids)}"

    barrier = threading.Barrier(N)
    attempts: Counter = Counter()
    lock = threading.Lock()

    def worker(staff_id: int) -> None:
        conn = connect(isolation)
        tries = 0
        use_barrier = barrier
        while True:
            tries += 1
            try:
                with conn.transaction():
                    count = active_count(conn)
                    if use_barrier is not None:
                        use_barrier.wait()
                    if count > 1:
                        conn.execute(
                            "UPDATE staff SET active = false WHERE staff_id = %s",
                            (staff_id,),
                        )
                break
            except psycopg.errors.SerializationFailure:
                # Retry the whole transaction from the start, and do not use
                # the barrier again (it has already been broken once).
                use_barrier = None
                continue
        with lock:
            attempts[tries] += 1
        conn.close()

    threads = [threading.Thread(target=worker, args=(sid,)) for sid in staff_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    check = connect(IsolationLevel.READ_COMMITTED)
    remaining = active_count(check)
    check.close()
    return remaining, attempts


def main() -> None:
    print("=" * 70)
    print("Task 4.1 - READ COMMITTED (expect 0 active staff: the rule is broken)")
    print("=" * 70)
    remaining, attempts = run(IsolationLevel.READ_COMMITTED)
    print(f"active staff of store 1 afterwards: {remaining}")
    print(f"transactions by number of attempts: {dict(sorted(attempts.items()))}")

    print()
    print("=" * 70)
    print("Task 4.3 - SERIALIZABLE with retries (expect exactly 1 active)")
    print("=" * 70)
    remaining, attempts = run(IsolationLevel.SERIALIZABLE)
    print(f"active staff of store 1 afterwards: {remaining}")
    print(f"transactions by number of attempts: {dict(sorted(attempts.items()))}")
    print(f"total serialisation retries: {sum((k - 1) * v for k, v in attempts.items())}")


if __name__ == "__main__":
    main()
