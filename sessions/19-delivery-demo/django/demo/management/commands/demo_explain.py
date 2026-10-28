import re

from django.core.management.base import BaseCommand
from django.db import connection

from demo.models import BIG_RENTAL_INDEXES, BigRental

QUERIES = {
    "big_rental_customer_rented": "SELECT * FROM big_rental WHERE customer_id = 42 ORDER BY rented_at DESC LIMIT 10",
    "big_rental_open": "SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days'",
}


def explain(sql: str) -> tuple[list[str], float]:
    with connection.cursor() as cur:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + sql)
        lines = [row[0] for row in cur.fetchall()]
    ms = float(re.search(r"Execution Time: ([\d.]+) ms", lines[-1]).group(1))
    return lines, ms


class Command(BaseCommand):
    help = "Demo 3: EXPLAIN (ANALYZE, BUFFERS) for the session 07 queries, without and with their index."

    def show(self, label: str, lines: list[str]) -> None:
        self.stdout.write(f"  {label}:")
        for line in lines:
            # The plan with its buffers, then the execution time; the planning lines are skipped.
            if line.startswith("Planning"):
                break
            self.stdout.write(f"    {line}")
        self.stdout.write(f"    {lines[-1]}")

    def handle(self, *args, **options):
        summary = []
        with connection.schema_editor() as editor:
            for index in BIG_RENTAL_INDEXES:
                editor.execute(f"DROP INDEX IF EXISTS {index.name}")

        for index in BIG_RENTAL_INDEXES:
            sql = QUERIES[index.name]
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{sql}"))
            before, before_ms = explain(sql)
            self.show("before", before)

            with connection.schema_editor() as editor:
                self.stdout.write(f"  index: {index.create_sql(BigRental, editor)}")
                editor.add_index(BigRental, index)
            after, after_ms = explain(sql)
            self.show("after", after)
            summary.append((index.name, before_ms, after_ms))

        self.stdout.write(self.style.MIGRATE_HEADING("\nSummary"))
        for name, before_ms, after_ms in summary:
            self.stdout.write(f"  {name:<28} {before_ms:>9.2f} ms -> {after_ms:>7.2f} ms  ({before_ms / after_ms:,.1f}x faster)")
