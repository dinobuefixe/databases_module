import time

from django.core.management.base import BaseCommand

from demo.derived import rebuild


class Command(BaseCommand):
    help = "Rebuilds every customer:{id}:films set from PostgreSQL. Redis holds nothing else to restore."

    def handle(self, *args, **options):
        start = time.perf_counter()
        customers = rebuild()
        self.stdout.write(self.style.SUCCESS(f"Rebuilt {customers} customers in {time.perf_counter() - start:.2f} s"))
