"""Create the daily_rentals materialised view and its unique index. Safe to run again."""

from app.db import SQL_DIR, pg_connect


def main() -> None:
    with pg_connect() as conn:
        conn.execute((SQL_DIR / "001_daily_rentals.sql").read_text())
        n = conn.execute("SELECT count(*) AS n FROM daily_rentals").fetchone()["n"]
    print(f"daily_rentals ready: {n} days")


if __name__ == "__main__":
    main()
