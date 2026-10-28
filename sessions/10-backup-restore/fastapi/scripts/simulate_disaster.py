"""Delete rows from three tables of this project's database, to have something to recover.

Only runs against a database whose name starts with s10_fastapi.

    uv run python -m scripts.simulate_disaster
"""

from app.db import DB_NAME, pg_connect
from scripts.common import require_own_database

# Three tables that no other table references with a foreign key, so each one can be
# recovered on its own with scripts.restore_table.
DISASTER = [
    ("payment", "DELETE FROM payment WHERE payment_date < '2023-01-01'"),
    ("film_actor", "DELETE FROM film_actor WHERE actor_id <= 50"),
    ("film_category", "DELETE FROM film_category WHERE category_id IN (1, 2, 3)"),
]


def main() -> None:
    require_own_database(DB_NAME)
    with pg_connect() as conn:
        for table, statement in DISASTER:
            deleted = conn.execute(statement).rowcount
            print(f"{statement:<62} -- {deleted} rows deleted")
    print(f"\n{DB_NAME} has lost data. To see where, run: uv run python -m scripts.verify {DB_NAME} <restored database>")


if __name__ == "__main__":
    main()
