import time
from pathlib import Path

from django.core.management.base import BaseCommand

from demo.pg import PG_USER, compose_exec, latest_dump, live_db, own


class Command(BaseCommand):
    help = "Restore a dump into a new database (default <db>_restored) and time it."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=Path, help="default: the latest file in backups/")
        parser.add_argument("--target", help="default: <your database>_restored")

    def handle(self, *args, dump, target, **options):
        dump = dump or latest_dump()
        target = own(target or f"{live_db()}_restored")
        if target == live_db():
            self.stderr.write("use restore_table to restore into the live database")
            return

        compose_exec("dropdb", "-U", PG_USER, "--if-exists", "--force", target)
        compose_exec("createdb", "-U", PG_USER, target)
        start = time.perf_counter()
        with dump.open("rb") as stdin:
            # --no-owner: objects belong to the user running the restore, so the
            # restore does not depend on the original roles existing.
            compose_exec("pg_restore", "-U", PG_USER, "-d", target, "--no-owner", stdin=stdin)
        self.stdout.write(f"restored {dump.name} into {target} in {time.perf_counter() - start:.1f} s")
