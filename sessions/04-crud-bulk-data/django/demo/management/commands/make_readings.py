import time

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Create the reading table with generate_series, reproducible with setseed."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=1_000_000)

    def handle(self, *args, rows, **options):
        start = time.perf_counter()
        # setseed applies to the current session, so both statements run on the
        # same connection, here inside one transaction.
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("SELECT setseed(0.42)")
            cur.execute("DROP TABLE IF EXISTS reading")
            cur.execute(
                """
                CREATE TABLE reading AS
                SELECT g AS reading_id,
                       now() - random() * interval '365 days' AS taken_at,
                       round((random() * 100)::numeric, 2)    AS value
                FROM generate_series(1, %s) AS g
                """,
                [rows],
            )
            cur.execute("SELECT count(*), sum(value) FROM reading")
            count, total = cur.fetchone()
        elapsed = time.perf_counter() - start
        # sum(value) is the same on every run: proof that the data is reproducible.
        self.stdout.write(f"reading: {count:,} rows in {elapsed:.2f} s, sum(value) = {total}")
