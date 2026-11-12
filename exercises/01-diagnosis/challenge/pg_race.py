"""The same race, handled by PostgreSQL.

10 processes, each with its own connection, insert the same 1,000 records into
the ``record`` table, one INSERT per record. The engine serialises the writes,
so no row is lost and the count is exactly 10,000 every run.

The table is emptied at the start so each run is independent, exactly like
``json_race.py`` resets the JSON file.

Run:  uv run python pg_race.py
"""

import multiprocessing as mp
import os

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:change-me-postgres@localhost:5432/ch01",
)

WORKERS = 10
PER_WORKER = 1_000

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS record (
    worker integer NOT NULL,
    n      integer NOT NULL
)
"""


def worker(worker_id: int) -> None:
    """Insert PER_WORKER rows on its own connection."""
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            for n in range(PER_WORKER):
                cur.execute(
                    "INSERT INTO record (worker, n) VALUES (%s, %s)",
                    (worker_id, n),
                )
        conn.commit()


def main() -> None:
    with psycopg.connect(DSN) as conn:
        conn.execute(CREATE_TABLE)
        conn.execute("TRUNCATE record")
        conn.commit()

    processes = [
        mp.Process(target=worker, args=(w,))
        for w in range(WORKERS)
    ]
    for p in processes:
        p.start()
    for p in processes:
        p.join()

    with psycopg.connect(DSN) as conn:
        count = conn.execute("SELECT count(*) FROM record").fetchone()[0]

    print(f"rows in record: {count}")
    print(f"expected:       {WORKERS * PER_WORKER}")


if __name__ == "__main__":
    main()
