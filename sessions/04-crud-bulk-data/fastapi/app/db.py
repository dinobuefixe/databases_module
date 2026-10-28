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


def create_tables() -> None:
    with pg_connect() as conn:
        conn.execute((SQL_DIR / "001_tables.sql").read_text())
