"""Demo 3: EXPLAIN (ANALYZE, BUFFERS) on big_rental before and after the session 07 indexes.

Run with: uv run python -m scripts.demo_explain [--plans]   (or make demo-explain)

The indexes are dropped first, so every run shows a real "before".
--plans prints the full plans, not only the summary.
"""

import argparse
import re

from sqlalchemy import text

from app.db import engine

QUERIES = {
    "last 10 rentals of customer 42": (
        "SELECT * FROM big_rental WHERE customer_id = 42 ORDER BY rented_at DESC LIMIT 10"
    ),
    "open rentals older than 30 days": (
        "SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days'"
    ),
}

INDEXES = {
    "big_rental_customer_rented": "CREATE INDEX big_rental_customer_rented ON big_rental (customer_id, rented_at DESC)",
    "big_rental_open": "CREATE INDEX big_rental_open ON big_rental (rented_at) WHERE returned_at IS NULL",
}


def explain(conn, sql: str) -> list[str]:
    return [row[0] for row in conn.execute(text(f"EXPLAIN (ANALYZE, BUFFERS) {sql}"))]  # fixed SQL above


def summary(plan: list[str]) -> str:
    """Main scan node, buffers read and execution time."""
    scan = next((line.strip().lstrip("-> ").split("  ")[0] for line in plan if "Scan" in line), "?")
    buffers = next((line.strip() for line in plan if line.strip().startswith("Buffers")), "")
    time_ms = next(float(m.group(1)) for line in plan if (m := re.search(r"Execution Time: ([\d.]+)", line)))
    return f"{time_ms:9.2f} ms  {scan[:55]:55}  {buffers}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plans", action="store_true")
    args = parser.parse_args()

    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        rows = conn.execute(text("SELECT count(*) FROM big_rental")).scalar_one()
        print(f"big_rental: {rows:,} rows\n")
        for name in INDEXES:
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))

        results = {}
        for phase in ("before", "after"):
            if phase == "after":
                for sql in INDEXES.values():
                    conn.execute(text(sql))
                conn.execute(text("ANALYZE big_rental"))
            for label, sql in QUERIES.items():
                plan = explain(conn, sql)
                results[(label, phase)] = plan
                if args.plans:
                    print(f"--- {label}, {phase} indexes\n" + "\n".join(plan) + "\n")

        for label in QUERIES:
            print(label)
            for phase in ("before", "after"):
                print(f"  {phase:6} {summary(results[(label, phase)])}")
            print()

        sizes = conn.execute(text("""
            SELECT relname, pg_size_pretty(pg_relation_size(oid))
            FROM pg_class WHERE relname IN ('big_rental', 'big_rental_customer_rented', 'big_rental_open')
            ORDER BY relname
        """)).all()
        print("sizes: " + ", ".join(f"{name} {size}" for name, size in sizes))


if __name__ == "__main__":
    main()
