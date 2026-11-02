"""Connect as each role and show what it can and cannot do. Every change is rolled back."""

import psycopg

from app.clients import DATABASE_URL, READONLY_DATABASE_URL

TESTS = {
    "app": [
        "SELECT count(*) FROM film",
        "INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')",
        "DROP TABLE film",
        "CREATE TABLE notes (id int)",
    ],
    "readonly": [
        "SELECT count(*) FROM film",
        "INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')",
        "DELETE FROM payment",
    ],
}


def main() -> None:
    for role, url in (("app", DATABASE_URL), ("readonly", READONLY_DATABASE_URL)):
        with psycopg.connect(url) as conn:
            user = conn.execute("SELECT current_user").fetchone()[0]
            print(f"\n== connected as {user}")
            for statement in TESTS[role]:
                try:
                    with conn.transaction(force_rollback=True):
                        cur = conn.execute(statement)
                        if cur.description:
                            result = cur.fetchone()[0]
                        else:
                            # rowcount is -1 for statements that change no rows, such as CREATE TABLE.
                            result = f"{cur.rowcount} row(s)" if cur.rowcount >= 0 else "done"
                    print(f"ALLOWED  {statement:<62} -> {result} (rolled back)")
                except psycopg.Error as exc:
                    # InsufficientPrivilege is the one this script is about; others are printed by name.
                    label = "REFUSED" if isinstance(exc, psycopg.errors.InsufficientPrivilege) else "FAILED"
                    print(f"{label:<8} {statement:<62} -> {type(exc).__name__}: {exc.diag.message_primary}")


if __name__ == "__main__":
    main()
