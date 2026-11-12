"""Bulk-load 1,000,000 valid, reproducible rows into Pagila's ``rental`` table.

Usage:
    uv run python seed.py <database>

The database name is the command-line argument (e.g. ``ch04_a``). The
connection credentials come from ``DATABASE_URL`` (the database name is
replaced by the argument), falling back to the default used in this module.

Guarantees:
- ``rental_id`` goes from 100,001 to 1,100,000, so two runs on different
  databases produce the same keys. The sequence is moved past the last id with
  ``setval`` afterwards.
- every ``inventory_id``, ``customer_id`` and ``staff_id`` exists in Pagila;
- ``rental_date`` is between 2022-01-01 and 2026-07-31;
- ``return_date`` is ``NULL`` or later than ``rental_date``;
- the unique index on (rental_date, inventory_id, customer_id) is respected:
  every ``rental_date`` is generated distinct, so no triple can repeat;
- a fixed random seed (42) makes the data reproducible;
- the script is idempotent: if the 1,000,000 rows already exist it changes
  nothing.

Performance: the load runs with ``session_replication_role = replica``, which
skips the foreign-key trigger checks (3 index lookups per row) during the
bulk load. This is only a speed-up for a load we know is valid: the unique
indexes, including the one on (rental_date, inventory_id, customer_id), stay
enforced, and the script re-checks every foreign key with a query right after
the load and aborts if any row is broken.
"""

from __future__ import annotations

import os
import random
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone

import psycopg

SEED = 42
ROWS = 1_000_000
FIRST_ID = 100_001
LAST_ID = FIRST_ID + ROWS - 1  # 1,100,000

START = datetime(2022, 1, 1, tzinfo=timezone.utc)
END = datetime(2026, 7, 31, 23, 59, 59, 999_999, tzinfo=timezone.utc)
SPAN_US = (END - START) // timedelta(microseconds=1)

DEFAULT_DSN = "postgresql://postgres:change-me-postgres@localhost:5432/pagila"

COPY_SQL = (
    "COPY rental (rental_id, rental_date, inventory_id, customer_id, "
    "return_date, staff_id) FROM STDIN"
)


def dsn_for(dbname: str) -> str:
    """Take DATABASE_URL and swap in the requested database name."""
    base = os.environ.get("DATABASE_URL", DEFAULT_DSN)
    parts = urllib.parse.urlsplit(base)
    return urllib.parse.urlunsplit(parts._replace(path="/" + dbname))


def rental_id_sequence(conn) -> str:
    """Return the sequence behind rental.rental_id.

    ``pg_get_serial_sequence`` only knows about sequences that are *owned* by
    the column. Pagila creates ``rental_rental_id_seq`` and wires it up with a
    plain ``DEFAULT nextval(...)`` instead of ``SERIAL``, so the ownership link
    is missing and ``pg_get_serial_sequence`` returns NULL. In that case fall
    back to parsing the column default (``nextval('rental_rental_id_seq'...)``).
    """
    seq = conn.execute(
        "SELECT pg_get_serial_sequence('rental', 'rental_id')"
    ).fetchone()[0]
    if seq:
        return seq

    default = conn.execute(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'rental' "
        "AND column_name = 'rental_id'"
    ).fetchone()[0]
    match = re.search(r"nextval\('([^']+)'", default or "")
    if not match:
        raise RuntimeError(f"cannot find rental_id sequence in default: {default!r}")
    return match.group(1)


def build_rows(rng: random.Random, inventories, customers, staffs):
    """Return the six columns as parallel lists, all reproducible from SEED."""
    # Distinct microsecond offsets -> distinct rental_date values -> the
    # unique index (rental_date, inventory_id, customer_id) can never clash.
    offsets = rng.sample(range(SPAN_US), ROWS)
    rental_dates = [START + timedelta(microseconds=us) for us in offsets]

    inventory_ids = rng.choices(inventories, k=ROWS)
    customer_ids = rng.choices(customers, k=ROWS)
    staff_ids = rng.choices(staffs, k=ROWS)

    return_dates: list[datetime | None] = []
    for rental_date in rental_dates:
        if rng.random() < 0.05:
            return_dates.append(None)
        else:
            return_dates.append(
                rental_date + timedelta(seconds=rng.uniform(3600, 30 * 86_400))
            )

    return rental_dates, inventory_ids, customer_ids, return_dates, staff_ids


def copy_lines(rental_dates, inventory_ids, customer_ids, return_dates, staff_ids):
    """Yield COPY text-format lines (tab separated, \\N for NULL)."""
    for i in range(ROWS):
        return_date = return_dates[i]
        return_text = "\\N" if return_date is None else str(return_date)
        yield (
            f"{FIRST_ID + i}\t{rental_dates[i]}\t{inventory_ids[i]}\t"
            f"{customer_ids[i]}\t{return_text}\t{staff_ids[i]}\n"
        )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run python seed.py <database>")

    dbname = sys.argv[1]
    dsn = dsn_for(dbname)
    rng = random.Random(SEED)

    with psycopg.connect(dsn) as conn:
        # --- idempotency: if the rows are already there, do nothing ---------
        existing = conn.execute(
            "SELECT count(*) FROM rental WHERE rental_id BETWEEN %s AND %s",
            (FIRST_ID, LAST_ID),
        ).fetchone()[0]
        if existing == ROWS:
            conn.execute(
                "SELECT setval(%s::regclass, %s, true)",
                (rental_id_sequence(conn), LAST_ID),
            )
            conn.commit()
            print(f"{dbname}: already seeded ({existing} rows), nothing changed")
            return
        if existing:
            conn.execute(
                "DELETE FROM rental WHERE rental_id BETWEEN %s AND %s",
                (FIRST_ID, LAST_ID),
            )
            conn.commit()

        # --- speed up the load: skip FK/trigger checks (needs superuser) ----
        # Unique indexes are NOT affected by this setting, so the unique index
        # on (rental_date, inventory_id, customer_id) is still enforced. The
        # foreign keys are verified with a query after the load.
        conn.execute("SET session_replication_role = replica")

        # --- valid foreign keys --------------------------------------------
        inventories = [
            r[0]
            for r in conn.execute(
                "SELECT inventory_id FROM inventory ORDER BY inventory_id"
            )
        ]
        customers = [
            r[0]
            for r in conn.execute(
                "SELECT customer_id FROM customer ORDER BY customer_id"
            )
        ]
        staffs = [
            r[0]
            for r in conn.execute("SELECT staff_id FROM staff ORDER BY staff_id")
        ]

        rental_dates, inventory_ids, customer_ids, return_dates, staff_ids = (
            build_rows(rng, inventories, customers, staffs)
        )

        # --- bulk load with COPY (batched text chunks) ----------------------
        with conn.cursor().copy(COPY_SQL) as copy:
            chunk: list[str] = []
            for line in copy_lines(
                rental_dates, inventory_ids, customer_ids, return_dates, staff_ids
            ):
                chunk.append(line)
                if len(chunk) >= 10_000:
                    copy.write("".join(chunk).encode())
                    chunk.clear()
            if chunk:
                copy.write("".join(chunk).encode())

        # --- verify every foreign key we skipped with a query ---------------
        # Because we loaded with session_replication_role = replica, the FK
        # triggers did not run. Re-check them explicitly and abort the
        # transaction if any of the new rows points to a missing parent.
        broken = conn.execute(
            """
            SELECT count(*)
            FROM rental r
            LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
            LEFT JOIN customer  c ON c.customer_id  = r.customer_id
            LEFT JOIN staff     s ON s.staff_id     = r.staff_id
            WHERE r.rental_id BETWEEN %s AND %s
              AND (i.inventory_id IS NULL
                   OR c.customer_id IS NULL
                   OR s.staff_id IS NULL)
            """,
            (FIRST_ID, LAST_ID),
        ).fetchone()[0]
        if broken:
            raise RuntimeError(f"foreign-key check failed: {broken} broken rows")

        # Back to normal trigger behaviour for the rest of the session.
        conn.execute("RESET session_replication_role")

        # --- move the sequence past the last explicit id -------------------
        conn.execute(
            "SELECT setval(%s::regclass, %s, true)",
            (rental_id_sequence(conn), LAST_ID),
        )
        conn.commit()

    print(f"{dbname}: inserted {ROWS} rentals ({FIRST_ID}..{LAST_ID})")


if __name__ == "__main__":
    main()
