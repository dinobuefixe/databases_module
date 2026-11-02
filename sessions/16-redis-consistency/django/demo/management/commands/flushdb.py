from django.core.management.base import BaseCommand

from demo.clients import r


class Command(BaseCommand):
    help = "Deletes every key in this project's Redis database (FLUSHDB), to test the rebuild."

    def handle(self, *args, **options):
        # FLUSHALL would empty every logical database on the server, including the
        # ones other projects use. FLUSHDB only empties the one in REDIS_URL.
        db = r.connection_pool.connection_kwargs.get("db", 0)
        r.flushdb()
        self.stdout.write(self.style.WARNING(f"FLUSHDB on Redis database {db}"))
