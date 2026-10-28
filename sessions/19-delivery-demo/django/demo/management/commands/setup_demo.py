import time
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from demo.models import Account


class Command(BaseCommand):
    help = "Prepares every demo: the account, the big_rental table (session 07) and the Redis sets."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=2_000_000)

    def handle(self, *args, rows, **options):
        Account.objects.update_or_create(id=1, defaults={"balance": Decimal("100")})
        self.stdout.write("account 1: balance 100")

        start = time.perf_counter()
        with connection.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS big_rental")
            # setseed makes random() repeat the same sequence, so every clone gets the same data.
            cur.execute("SELECT setseed(0.1)")
            cur.execute(
                """
                CREATE TABLE big_rental AS
                SELECT g AS id,
                       (random() * 599 + 1)::int                          AS customer_id,
                       now() - random() * interval '3 years'              AS rented_at,
                       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
                FROM generate_series(1, %s) AS g
                """,
                [rows],
            )
            # After a bulk load: statistics for the planner, and the visibility map that lets
            # PostgreSQL answer some queries from the index alone (Index Only Scan).
            cur.execute("VACUUM ANALYZE big_rental")
        self.stdout.write(f"big_rental: {rows:,} rows in {time.perf_counter() - start:.1f} s")

        call_command("demo_rebuild", "--no-flush", stdout=self.stdout)
