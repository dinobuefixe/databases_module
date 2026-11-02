"""Create big_rental with a reproducible random sample (default 2,000,000 rows).

    uv run python -m scripts.create_big_rental
    uv run python -m scripts.create_big_rental --rows 500000
"""

import argparse
import time

from app.db import pg_connect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=2_000_000)
    args = parser.parse_args()

    started = time.perf_counter()
    with pg_connect() as conn:
        conn.execute("DROP TABLE IF EXISTS big_rental")
        conn.execute("SELECT setseed(0.1)")
        conn.execute(
            """
            CREATE TABLE big_rental AS
            SELECT g AS id,
                   (random() * 599 + 1)::int                 AS customer_id,
                   now() - random() * interval '3 years'      AS rented_at,
                   CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
            FROM generate_series(1, %s) AS g
            """,
            (args.rows,),
        )
    # VACUUM cannot run inside a transaction, so it gets its own autocommit connection.
    with pg_connect(autocommit=True) as conn:
        # ANALYZE gives the planner fresh statistics: the table's size and value distribution.
        # The tutorial runs ANALYZE only. Autovacuum would also VACUUM a freshly loaded table
        # within a minute or so; doing it now makes the plans the same on every run.
        conn.execute("VACUUM ANALYZE big_rental")
        size = conn.execute("SELECT pg_size_pretty(pg_relation_size('big_rental')) AS s").fetchone()["s"]
    print(f"big_rental: {args.rows:,} rows, {size}, in {time.perf_counter() - started:.1f} s")
    print("No indexes yet. Run the EXPLAIN now to see the plan before.")


if __name__ == "__main__":
    main()
