import time

from django.core.management.base import BaseCommand
from django.db import connection

from demo import indexes

BIG_RENTAL_INDEXES = ["big_rental_customer_rented", "big_rental_open"]
# Dropped during both inserts so it does not count, then put back if it was there.
OTHER_INDEXES = ["big_rental_rented"]


def timed_insert(rows: int) -> float:
    """The tutorial's INSERT of extra rows, timed, then removed again."""
    with connection.cursor() as cur:
        cur.execute("SELECT max(id) FROM big_rental")
        first = cur.fetchone()[0] + 1
        start = time.perf_counter()
        cur.execute(
            "INSERT INTO big_rental SELECT g, 1, now(), NULL FROM generate_series(%s, %s) g",
            [first, first + rows - 1],
        )
        elapsed = time.perf_counter() - start
        cur.execute("DELETE FROM big_rental WHERE id >= %s", [first])
        cur.execute("VACUUM big_rental")
    return elapsed


class Command(BaseCommand):
    help = "Time the same INSERT without and with the big_rental indexes."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=100_000)

    def handle(self, *args, rows, **options):
        before = indexes.existing()

        for name in BIG_RENTAL_INDEXES + OTHER_INDEXES:
            if name in indexes.existing():
                indexes.drop(name)
        without = timed_insert(rows)

        for name in BIG_RENTAL_INDEXES:
            indexes.create(name)
        with_indexes = timed_insert(rows)

        # Leave the indexes as they were.
        for name in BIG_RENTAL_INDEXES:
            if name not in before:
                indexes.drop(name)
        for name in OTHER_INDEXES:
            if name in before:
                indexes.create(name)

        self.stdout.write(f"INSERT {rows:,} rows without indexes: {without * 1000:8.0f} ms")
        self.stdout.write(f"INSERT {rows:,} rows with {len(BIG_RENTAL_INDEXES)} indexes: {with_indexes * 1000:8.0f} ms ({with_indexes / without:.1f}x)")
