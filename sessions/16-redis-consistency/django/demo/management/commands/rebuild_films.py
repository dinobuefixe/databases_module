import time

from django.core.management.base import BaseCommand

from demo.derived import rebuild_per_customer, rebuild_single_query


class Command(BaseCommand):
    help = "Rebuilds every customer:{id}:films set from PostgreSQL and prints how long it took."

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["per-customer", "single-query", "both"], default="both")

    def handle(self, *args, mode, **options):
        modes = {"per-customer": rebuild_per_customer, "single-query": rebuild_single_query}
        for name, fn in modes.items():
            if mode in (name, "both"):
                start = time.perf_counter()
                customers = fn()
                elapsed = time.perf_counter() - start
                self.stdout.write(self.style.SUCCESS(f"{name:<13} {customers} customers in {elapsed:.2f} s"))
