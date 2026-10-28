"""Break the rules on purpose and print what the database says each time.

Everything runs inside one transaction that is rolled back at the end,
so the script can be run again and leaves the data as it found it.
"""

import psycopg

from app.db import pg_connect


def attempt(conn: psycopg.Connection, label: str, sql: str, params: tuple = ()) -> None:
    print(f"\n-- {label}\n{sql.strip()}" + (f"  params: {params}" if params else ""))
    try:
        # A nested transaction is a SAVEPOINT: a failure undoes this statement only.
        with conn.transaction():
            cur = conn.execute(sql, params)
        print(f"OK: {cur.rowcount} row(s)")
    except psycopg.errors.IntegrityError as exc:
        print(f"ERROR: {exc.diag.message_primary}")
        if exc.diag.message_detail:
            print(f"DETAIL: {exc.diag.message_detail}")
        print(f"constraint: {exc.diag.constraint_name}")


def count_lines(conn: psycopg.Connection, recipe_id: int) -> int:
    return conn.execute(
        "SELECT count(*) AS n FROM recipe_ingredient WHERE recipe_id = %s", (recipe_id,)
    ).fetchone()["n"]


def main() -> None:
    with pg_connect() as conn:
        with conn.transaction() as outer:
            # Data for the delete tests, created here so the script does not depend on the seed.
            author_id = conn.execute(
                "INSERT INTO author (name, email) VALUES ('Test author', 'test.author@example.com') RETURNING author_id"
            ).fetchone()["author_id"]
            recipe_id = conn.execute(
                "INSERT INTO recipe (author_id, title, servings) VALUES (%s, 'Test soup', 2) RETURNING recipe_id",
                (author_id,),
            ).fetchone()["recipe_id"]
            conn.execute(
                """
                INSERT INTO ingredient (name, kcal_per_100g) VALUES ('Test leek', 31), ('Test potato', 77);
                """
            )
            conn.execute(
                """
                INSERT INTO recipe_ingredient (recipe_id, ingredient_id, grams)
                SELECT %s, ingredient_id, 300 FROM ingredient WHERE name LIKE 'Test %%'
                """,
                (recipe_id,),
            )

            attempt(conn, "CHECK: negative calories",
                    "INSERT INTO ingredient (name, kcal_per_100g) VALUES ('Sugar', -1)")
            attempt(conn, "FOREIGN KEY: author 999 does not exist",
                    "INSERT INTO recipe (author_id, title, servings) VALUES (999, 'Soup', 4)")
            attempt(conn, "UNIQUE: the same email twice",
                    "INSERT INTO author (name, email) VALUES ('Ana', 'ana@example.com'), ('Ana 2', 'ana@example.com')")
            attempt(conn, "UNIQUE (author_id, title): the same author publishes the same title twice",
                    "INSERT INTO recipe (author_id, title, servings) VALUES (%s, 'Test soup', 4)", (author_id,))

            attempt(conn, "ON DELETE RESTRICT: delete an author who has recipes",
                    "DELETE FROM author WHERE author_id = %s", (author_id,))

            print(f"\nrecipe {recipe_id} has {count_lines(conn, recipe_id)} ingredient lines before the delete")
            attempt(conn, "ON DELETE CASCADE: delete the recipe",
                    "DELETE FROM recipe WHERE recipe_id = %s", (recipe_id,))
            print(f"recipe {recipe_id} has {count_lines(conn, recipe_id)} ingredient lines after the delete")

            # Undo the test data and anything that succeeded.
            raise psycopg.Rollback(outer)
    print("\nRolled back: the database is unchanged.")


if __name__ == "__main__":
    main()
