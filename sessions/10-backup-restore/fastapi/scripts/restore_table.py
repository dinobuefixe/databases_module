"""Restore one table from a dump into this project's database.

    uv run python -m scripts.restore_table payment
    uv run python -m scripts.restore_table film_actor --file backups/x.dump
    uv run python -m scripts.restore_table payment --clean     # the tutorial's command, see the README

Default (data only): TRUNCATE the table, then load its rows from the dump with
pg_restore --data-only. The table's definition, indexes and the views that use it stay as they are.
For a partitioned table such as payment, the rows live in the partitions, so each partition
is named with its own -t.

--clean: pg_restore --clean -t <table>, as in the tutorial. It drops and recreates the table,
which fails when views or foreign keys depend on it, as they do on most Pagila tables.
"""

import argparse
from pathlib import Path

from psycopg import sql

from app.db import DB_NAME, pg_connect
from scripts.common import compose_exec, latest_dump, require_own_database


def partitions(table: str) -> list[str]:
    with pg_connect() as conn:
        return [
            r["name"]
            for r in conn.execute(
                "SELECT inhrelid::regclass::text AS name FROM pg_inherits WHERE inhparent = %s::regclass ORDER BY 1",
                (table,),
            )
        ]


def count(table: str) -> int:
    with pg_connect() as conn:
        return conn.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table))).fetchone()["n"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("table")
    parser.add_argument("--file", type=Path, help="defaults to the newest dump in backups/")
    parser.add_argument("--clean", action="store_true", help="run the tutorial's pg_restore --clean -t instead")
    args = parser.parse_args()

    require_own_database(DB_NAME)
    dump = args.file or latest_dump()
    before = count(args.table)

    if args.clean:
        with dump.open("rb") as stdin:
            result = compose_exec(
                "pg_restore", "-U", "postgres", "-d", DB_NAME, "--clean", "-t", args.table, stdin=stdin, check=False
            )
        print(f"pg_restore --clean exit code {result.returncode}")
    else:
        names = [args.table, *partitions(args.table)]
        with pg_connect() as conn:
            # TRUNCATE refuses if another table has a foreign key to this one: then this
            # simple method does not apply, and you restore into a new database and copy rows.
            conn.execute(sql.SQL("TRUNCATE {}").format(sql.Identifier(args.table)))
        selectors = [arg for name in names for arg in ("-t", name)]
        with dump.open("rb") as stdin:
            compose_exec("pg_restore", "-U", "postgres", "-d", DB_NAME, "--data-only", *selectors, stdin=stdin)

    print(f"{args.table}: {before} rows before, {count(args.table)} rows after (from {dump.name})")


if __name__ == "__main__":
    main()
