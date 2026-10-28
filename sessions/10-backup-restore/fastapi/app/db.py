import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
DB_NAME = psycopg.conninfo.conninfo_to_dict(DATABASE_URL)["dbname"]


def pg_connect(dbname: str | None = None) -> psycopg.Connection:
    """Connect to this project's database, or to another one on the same server."""
    return psycopg.connect(DATABASE_URL, dbname=dbname or DB_NAME, row_factory=dict_row)


def row_counts(dbname: str | None = None) -> dict[str, int]:
    """Exact row count of every table in the public schema.

    A partitioned table (payment) is counted once through its parent, not per partition.
    """
    with pg_connect(dbname) as conn:
        tables = [
            r["relname"]
            for r in conn.execute(
                """
                SELECT c.relname FROM pg_class c
                WHERE c.relnamespace = 'public'::regnamespace
                  AND c.relkind IN ('r', 'p') AND NOT c.relispartition
                ORDER BY c.relname
                """
            )
        ]
        return {
            t: conn.execute(psycopg.sql.SQL("SELECT count(*) AS n FROM {}").format(psycopg.sql.Identifier(t))).fetchone()["n"]
            for t in tables
        }
