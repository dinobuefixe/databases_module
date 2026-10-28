"""Measure what the indexes cost on INSERT.

Inserts N rows into big_rental (the tutorial's INSERT) with no tutorial index, with each one,
and with both, then rolls back each time so the table does not grow.
The indexes are put back as they were at the start.

    uv run python -m scripts.write_cost --rows 100000
"""

import argparse
import statistics
import time

from app.db import pg_connect
from app.indexes import INDEXES, create_sql, drop_sql

# The expression index is on customer, not big_rental. "single" is dropped in every case so it does not count.
TABLE_INDEXES = ["composite", "partial", "single"]
CASES = [[], ["composite"], ["partial"], ["composite", "partial"]]


def existing(conn) -> set[str]:
    names = [INDEXES[key].name for key in TABLE_INDEXES]
    found = {r["indexname"] for r in conn.execute("SELECT indexname FROM pg_indexes WHERE indexname = ANY(%s)", (names,))}
    return {key for key in TABLE_INDEXES if INDEXES[key].name in found}


def set_indexes(conn, wanted: list[str]) -> None:
    for key in TABLE_INDEXES:
        conn.execute(create_sql(key) if key in wanted else drop_sql(key))


def time_insert(conn, rows: int, repeat: int) -> float:
    first_id = conn.execute("SELECT max(id) + 1 AS n FROM big_rental").fetchone()["n"]
    timings = []
    for _ in range(repeat):
        conn.execute("BEGIN")
        started = time.perf_counter()
        conn.execute(
            "INSERT INTO big_rental SELECT g, 1, now(), NULL FROM generate_series(%s, %s) g",
            (first_id, first_id + rows - 1),
        )
        timings.append(time.perf_counter() - started)
        conn.execute("ROLLBACK")
        # The rolled-back rows stay in the table as dead tuples until VACUUM clears them.
        conn.execute("VACUUM big_rental")
    return statistics.median(timings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--repeat", type=int, default=3, help="runs per case; the median is printed")
    args = parser.parse_args()

    with pg_connect(autocommit=True) as conn:
        at_start = existing(conn)
        try:
            baseline = None
            for case in CASES:
                set_indexes(conn, case)
                elapsed = time_insert(conn, args.rows, args.repeat)
                baseline = baseline or elapsed
                label = " + ".join(case) or "no tutorial index"
                print(f"{label:<22} {elapsed * 1000:8.0f} ms   {elapsed / baseline:4.1f}x")
        finally:
            print("restoring the indexes that existed at the start...")
            set_indexes(conn, sorted(at_start))


if __name__ == "__main__":
    main()
