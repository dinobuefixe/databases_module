"""Bulk data, reproducible with a fixed seed.

    uv run python -m scripts.bulk_load person --rows 100000
    uv run python -m scripts.bulk_load reading --rows 1000000
"""

import argparse
import time

from faker import Faker

from app.db import create_tables, pg_connect

INSERT_PERSON = "INSERT INTO person (name, email, city) VALUES (%s, %s, %s)"


def make_people(n: int) -> list[tuple[str, str, str]]:
    # The same seed gives the same people on every machine and every run.
    Faker.seed(42)
    fake = Faker("en_GB")
    return [(fake.name(), fake.unique.email(), fake.city()) for _ in range(n)]


def load_copy(cur, rows) -> None:
    # COPY streams every row in one command.
    with cur.copy("COPY person (name, email, city) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)


def load_executemany(cur, rows) -> None:
    # psycopg sends the INSERTs in pipeline mode: no wait for each reply.
    cur.executemany(INSERT_PERSON, rows)


def load_one_by_one(cur, rows) -> None:
    # One INSERT and one round trip per row.
    for row in rows:
        cur.execute(INSERT_PERSON, row)


METHODS = {"copy": load_copy, "executemany": load_executemany, "insert": load_one_by_one}


def person(rows: int, methods: list[str]) -> None:
    create_tables()
    started = time.perf_counter()
    people = make_people(rows)
    print(f"generated {rows:,} people with Faker in {time.perf_counter() - started:.1f} s")

    results = []
    for name in methods:
        with pg_connect() as conn:
            conn.execute("TRUNCATE person RESTART IDENTITY")
            conn.commit()
            started = time.perf_counter()
            with conn.cursor() as cur:
                METHODS[name](cur, people)
            conn.commit()  # all three methods load inside one transaction
            elapsed = time.perf_counter() - started
            count = conn.execute("SELECT count(*) AS n FROM person").fetchone()["n"]
        results.append((name, elapsed, count))
        print(f"{name:<12} {elapsed:8.2f} s  {count / elapsed:>10,.0f} rows/s  ({count:,} rows)")

    fastest = min(r[1] for r in results)
    for name, elapsed, _ in results:
        print(f"{name:<12} {elapsed / fastest:5.1f}x the fastest")


def reading(rows: int) -> None:
    started = time.perf_counter()
    with pg_connect() as conn:
        # setseed applies to this session, so it must run on the same connection as random().
        conn.execute("SELECT setseed(0.42)")
        conn.execute("DROP TABLE IF EXISTS reading")
        conn.execute(
            """
            CREATE TABLE reading AS
            SELECT g AS reading_id,
                   now() - random() * interval '365 days' AS taken_at,
                   round((random() * 100)::numeric, 2)    AS value
            FROM generate_series(1, %s) AS g
            """,
            (rows,),
        )
        summary = conn.execute("SELECT count(*) AS n, sum(value) AS total FROM reading").fetchone()
    print(f"reading: {summary['n']:,} rows in {time.perf_counter() - started:.1f} s")
    # taken_at depends on now(), but value only on the seed: this total is the same on every run.
    print(f"sum(value) = {summary['total']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="table", required=True)
    p = sub.add_parser("person", help="Faker rows loaded with COPY, executemany and one INSERT per row")
    p.add_argument("--rows", type=int, default=100_000)
    p.add_argument("--methods", default="copy,executemany,insert", help="comma-separated, in order")
    r = sub.add_parser("reading", help="generate_series rows created in SQL")
    r.add_argument("--rows", type=int, default=1_000_000)
    args = parser.parse_args()

    if args.table == "person":
        person(args.rows, args.methods.split(","))
    else:
        reading(args.rows)


if __name__ == "__main__":
    main()
