from django.core.management.base import BaseCommand
from django.db import connection, transaction

from demo.pg import live_db

# A DELETE with the wrong WHERE, on three tables. Only rows that nothing else
# references, so the deletes succeed as they would in a real accident.
DISASTER = [
    ("film_actor", "DELETE FROM film_actor WHERE actor_id <= 50"),
    ("film_category", "DELETE FROM film_category WHERE category_id IN (1, 2, 3)"),
    ("payment", "DELETE FROM payment WHERE payment_date < '2022-03-01'"),
]


class Command(BaseCommand):
    help = "Delete rows from three tables of this project's database (and only this one)."

    def handle(self, *args, **options):
        self.stdout.write(f"database: {live_db()}")
        with transaction.atomic(), connection.cursor() as cur:
            for table, statement in DISASTER:
                cur.execute(statement)
                self.stdout.write(f"{statement:<60} -> {cur.rowcount:>5} rows deleted")
        self.stdout.write("Run `uv run python manage.py verify` to see the damage.")
