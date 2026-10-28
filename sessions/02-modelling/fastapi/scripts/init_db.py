"""Create the four tables and load the seed. Run again to start from scratch."""

from pathlib import Path

from app.db import pg_connect

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def main() -> None:
    with pg_connect() as conn:
        for name in ("schema.sql", "seed.sql"):
            conn.execute((SQL_DIR / name).read_text())
            print(f"applied {name}")
        for row in conn.execute("SELECT recipe_id, title, servings, kcal_per_serving FROM recipe ORDER BY recipe_id"):
            print(row)


if __name__ == "__main__":
    main()
