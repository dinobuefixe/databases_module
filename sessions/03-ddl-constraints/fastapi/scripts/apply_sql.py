"""Apply the numbered scripts in sql/ in order, each one once.

The applied_script table records what has run, so running this again only applies new files.
Session 12 replaces this with Alembic, which works the same way.
"""

from pathlib import Path

from app.db import pg_connect

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def main() -> None:
    with pg_connect() as conn:
        # Autocommit, so each conn.transaction() below is a real transaction of its own.
        conn.autocommit = True
        conn.execute(
            "CREATE TABLE IF NOT EXISTS applied_script (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {row["name"] for row in conn.execute("SELECT name FROM applied_script")}

        for path in sorted(SQL_DIR.glob("[0-9][0-9][0-9]_*.sql")):
            if path.name in done:
                print(f"skip   {path.name} (already applied)")
                continue
            # Each script and its record commit together, or not at all.
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO applied_script (name) VALUES (%s)", (path.name,))
            print(f"apply  {path.name}")


if __name__ == "__main__":
    main()
