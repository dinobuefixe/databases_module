from django.core.management.base import BaseCommand
from django.db import connection

from demo.clients import mongo_db

TABLES = ["account", "customer", "inventory", "rental", "payment"]


class Command(BaseCommand):
    help = "Prints row counts, document counts and one known query, for the runbook's verification step."

    def handle(self, *args, **options):
        # One line per fact, sorted, so two runs can be compared with diff.
        with connection.cursor() as cur:
            for table in TABLES:
                cur.execute(f'SELECT count(*) FROM "{table}"')  # table names from the list above, not input
                self.stdout.write(f"postgres {table} {cur.fetchone()[0]}")
            # A known query: the answer for customer 1 must survive a restore.
            cur.execute("SELECT count(*), coalesce(sum(amount), 0) FROM payment WHERE customer_id = %s", [1])
            n, total = cur.fetchone()
            self.stdout.write(f"postgres query:customer_1_payments {n} {total}")
        for name in sorted(mongo_db.list_collection_names()):
            self.stdout.write(f"mongo {name} {mongo_db[name].count_documents({})}")
