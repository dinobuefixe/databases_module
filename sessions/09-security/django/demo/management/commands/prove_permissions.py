from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connections, transaction


class Rollback(Exception):
    pass


class Command(BaseCommand):
    help = "Connect as app, readonly and migrations and check what each one may do."

    def attempt(self, alias: str, statements: list[str], should_work: bool, expect_row: tuple | None = None) -> bool:
        """Run statements as one role inside a transaction that is always rolled back."""
        try:
            with transaction.atomic(using=alias), connections[alias].cursor() as cur:
                for statement in statements:
                    cur.execute(statement)
                raise Rollback(cur.fetchone() if cur.description else None)
        except Rollback as done:
            row = done.args[0]
            worked = expect_row is None or row == expect_row
            detail = f"ok {row or ''}".strip()
        except DatabaseError as exc:
            worked, detail = False, str(exc).splitlines()[0]
        passed = worked == should_work
        expected = "allowed" if should_work else "refused"
        self.stdout.write(f"{'PASS' if passed else 'FAIL'}  {alias:<10} {expected:<8} {'; '.join(statements)}\n      -> {detail}")
        return passed

    def handle(self, *args, **options):
        results = [
            self.attempt("default", ["SELECT current_user, count(*) FROM film"], True),
            self.attempt("default", ["INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y') RETURNING actor_id"], True),
            self.attempt("default", ["DROP TABLE film"], False),
            self.attempt("default", ["CREATE TABLE app_was_here (id int)"], False),
            self.attempt("readonly", ["SELECT current_user, count(*) FROM actor"], True),
            self.attempt("readonly", ["INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')"], False),
            self.attempt("readonly", ["DELETE FROM payment"], False),
            # Default privileges: a table created by migrations can be used by app and
            # readonly without another GRANT. Checked inside the same rolled-back transaction.
            self.attempt(
                "migrations",
                [
                    "CREATE TABLE new_table (id int)",
                    "SELECT has_table_privilege('app', 'new_table', 'INSERT'), "
                    "has_table_privilege('readonly', 'new_table', 'SELECT'), "
                    "has_table_privilege('readonly', 'new_table', 'INSERT')",
                ],
                True,
                expect_row=(True, True, False),
            ),
        ]
        if not all(results):
            raise CommandError("some permissions are not what the tutorial expects")
        self.stdout.write("\nAll permission checks passed.")
