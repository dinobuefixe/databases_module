"""Prepares everything the demos need. Safe to run again.

Run with: uv run python -m scripts.setup [--force-big-rental]

- account table (session 08) with account 1 at 100
- big_rental (session 07), BIG_RENTAL_ROWS rows, built with setseed so every run is the same, then VACUUM ANALYZE
- customer:{id}:films sets in Redis (session 16)
"""

import argparse
import os
import time
from decimal import Decimal

from sqlalchemy import text

from app.db import SessionLocal, engine
from app.films_sets import rebuild_all
from app.models import Account, Base

BIG_RENTAL_SQL = """
CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, {rows}) AS g
"""


def big_rental(rows: int, force: bool) -> None:
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('big_rental') IS NOT NULL")).scalar_one()
        if exists and not force:
            count = conn.execute(text("SELECT count(*) FROM big_rental")).scalar_one()
            if count == rows:
                print(f"big_rental already has {rows:,} rows")
                return
        start = time.perf_counter()
        conn.execute(text("DROP TABLE IF EXISTS big_rental"))
        # setseed and the CREATE must run on the same connection to get the same rows.
        conn.execute(text("SELECT setseed(0.1)"))
        # CREATE TABLE AS takes no bound parameters; rows is an int, so formatting is safe.
        conn.execute(text(BIG_RENTAL_SQL.format(rows=int(rows))))
    # VACUUM (outside a transaction) sets the hint bits and the visibility map now,
    # so the first demo-explain does not pay for that and look slower than it is.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("VACUUM ANALYZE big_rental"))
    print(f"big_rental created with {rows:,} rows in {time.perf_counter() - start:.1f} s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-big-rental", action="store_true")
    args = parser.parse_args()

    Base.metadata.create_all(engine, tables=[Account.__table__])
    with SessionLocal.begin() as session:
        if session.get(Account, 1) is None:
            session.add(Account(id=1, balance=Decimal("100")))
    print("account table ready")

    big_rental(int(os.getenv("BIG_RENTAL_ROWS", "2000000")), args.force_big_rental)

    with SessionLocal() as session:
        print("redis sets rebuilt for", rebuild_all(session), "customers")


if __name__ == "__main__":
    main()
