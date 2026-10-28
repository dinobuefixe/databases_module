import subprocess
import time
from pathlib import Path

from django.core.management.base import BaseCommand

from demo.pg import PG_USER, compose_exec, latest_dump, live_db


class Command(BaseCommand):
    help = "Empty one or more tables and load their rows from a dump, in one transaction."

    def add_arguments(self, parser):
        parser.add_argument("tables", nargs="+", help="for payment, name the partitions: payment_p2022_01 ...")
        parser.add_argument("--dump", type=Path, help="default: the latest file in backups/")

    def handle(self, *args, tables, dump, **options):
        dump = dump or latest_dump()

        # The tutorial's two steps are TRUNCATE film_actor, then
        # pg_restore --data-only -t film_actor. Here they run in one psql
        # transaction (-1): pg_restore writes the data as a COPY script instead of
        # loading it, and psql runs TRUNCATE + COPY together, so a failure leaves
        # the table as it was instead of empty.
        selection = [arg for table in tables for arg in ("-t", table)]
        with dump.open("rb") as stdin:
            script = compose_exec("pg_restore", "--data-only", *selection, "-f", "-", stdin=stdin, stdout=subprocess.PIPE).stdout
        if b"COPY " not in script:
            self.stderr.write(f"no data for {tables} in {dump.name} (a partitioned table keeps its rows in the partitions)")
            raise SystemExit(1)

        truncate = f"TRUNCATE {', '.join(f'public.{t}' for t in tables)};\n".encode()
        start = time.perf_counter()
        compose_exec("psql", "-U", PG_USER, "-d", live_db(), "-1", "-v", "ON_ERROR_STOP=1", "-q", input=truncate + script, stdout=subprocess.DEVNULL)
        self.stdout.write(f"restored the rows of {', '.join(tables)} from {dump.name} in {time.perf_counter() - start:.2f} s")
