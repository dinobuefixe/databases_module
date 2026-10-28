"""Applies the SQL files in sql/ in order. The seed only runs on an empty table.

Run with: uv run python -m scripts.init_db
"""

from pathlib import Path

from sqlalchemy import text

from app.db import engine

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

with engine.begin() as conn:
    conn.exec_driver_sql((SQL_DIR / "001_film_review.sql").read_text())
    if conn.execute(text("SELECT count(*) FROM film_review")).scalar_one() == 0:
        conn.exec_driver_sql((SQL_DIR / "002_seed_reviews.sql").read_text())
    print("film_review rows:", conn.execute(text("SELECT count(*) FROM film_review")).scalar_one())
