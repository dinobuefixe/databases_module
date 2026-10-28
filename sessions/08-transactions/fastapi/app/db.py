import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def pg_connect(**kwargs) -> psycopg.Connection:
    # One connection per call keeps the example simple. Session 11 introduces a pool.
    # Leaving the `with` block commits, or rolls back if an exception was raised.
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, **kwargs)



def run_sql_file(name: str) -> None:
    """Run one of the files in sql/. Each one is safe to run again."""
    with pg_connect() as conn:
        conn.execute((SQL_DIR / name).read_text())
