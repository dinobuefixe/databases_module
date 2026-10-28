import sys
import time

from django.core.management.base import BaseCommand

from demo.clients import r
from demo.derived import rebuild, verify


class Command(BaseCommand):
    help = "Demo 2: empty Redis, show the verification failing, rebuild from PostgreSQL, verify again."

    def add_arguments(self, parser):
        parser.add_argument("--no-flush", action="store_true", help="rebuild and verify only")

    def report(self, label: str) -> bool:
        checked, errors = verify()
        if errors:
            self.stdout.write(self.style.ERROR(f"{label}: {len(errors)} of {checked} customers differ, e.g. {errors[0]}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"{label}: all {checked} customers match PostgreSQL"))
        return not errors

    def handle(self, *args, no_flush, **options):
        if not no_flush:
            # FLUSHDB empties only this project's Redis database. The demo in your own
            # environment uses FLUSHALL; here other projects share the server.
            r.flushdb()
            self.stdout.write(f"FLUSHDB on Redis database {r.connection_pool.connection_kwargs.get('db', 0)}: {r.dbsize()} keys left")
            self.report("verify before rebuild")

        start = time.perf_counter()
        customers = rebuild()
        self.stdout.write(f"rebuild: {customers} customers in {time.perf_counter() - start:.2f} s (one query, one pipeline)")

        if not self.report("verify after rebuild"):
            sys.exit(1)
