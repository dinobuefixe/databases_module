import time

from django.core.management.base import BaseCommand
from django.db import connection, transaction

# Plain SQL: Django has no way to say CREATE TABLE ... AS SELECT ... generate_series.
CREATE = """
CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, %s) AS g
"""


class Command(BaseCommand):
    help = "Create big_rental with random but reproducible rows (setseed 0.1)."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=2_000_000)

    def handle(self, *args, rows, **options):
        start = time.perf_counter()
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS big_rental")
            cur.execute("SELECT setseed(0.1)")  # same session as the CREATE, so the same data every time
            cur.execute(CREATE, [rows])
        with connection.cursor() as cur:
            # VACUUM marks the new pages all-visible (as autovacuum would do a little later);
            # ANALYZE gives the planner fresh statistics.
            cur.execute("VACUUM ANALYZE big_rental")
            cur.execute("SELECT count(*), pg_size_pretty(pg_relation_size('big_rental')) FROM big_rental")
            count, size = cur.fetchone()
        self.stdout.write(f"big_rental: {count:,} rows, {size}, {time.perf_counter() - start:.1f} s")
