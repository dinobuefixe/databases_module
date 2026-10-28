import subprocess
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from demo.counts import row_counts
from demo.pg import latest_dump, live_db

# Throwaway container, removed when stopped (--rm). Its port is published on
# 127.0.0.1 only, in this project's range, so the row counts can be read from here.
CONTAINER = "s10-django-pgtest"
PORT = 55201
PASSWORD = "test"


def docker(*args: str, stdin=None) -> str:
    print("$ docker", " ".join(args))
    result = subprocess.run(["docker", *args], stdin=stdin, capture_output=True)
    if result.returncode != 0:
        raise CommandError(result.stderr.decode())
    return result.stdout.decode()


class Command(BaseCommand):
    help = "Restore the latest dump into a brand new postgres:18 container and compare row counts."

    def add_arguments(self, parser):
        parser.add_argument("--dump", type=Path, help="default: the latest file in backups/")

    def handle(self, *args, dump, **options):
        dump = dump or latest_dump()
        # No volume, no roles, no settings from your setup: only the dump.
        docker("run", "--rm", "-d", "--name", CONTAINER, "-e", f"POSTGRES_PASSWORD={PASSWORD}",
               "-p", f"127.0.0.1:{PORT}:5432", "postgres:18")
        try:
            # The image starts a temporary server for initdb and then the real one;
            # wait until the real one answers on TCP.
            docker("exec", CONTAINER, "sh", "-c", "until pg_isready -h 127.0.0.1 -U postgres -q; do sleep 1; done")
            docker("exec", CONTAINER, "createdb", "-U", "postgres", "pagila")
            start = time.perf_counter()
            with dump.open("rb") as stdin:
                docker("exec", "-i", CONTAINER, "pg_restore", "-U", "postgres", "-d", "pagila", "--no-owner", stdin=stdin)
            elapsed = time.perf_counter() - start
            known = docker("exec", CONTAINER, "psql", "-U", "postgres", "-d", "pagila", "-tAc", "SELECT count(*) FROM rental;").strip()
            restored = row_counts("pagila", host="127.0.0.1", port=PORT, user="postgres", password=PASSWORD)
        finally:
            subprocess.run(["docker", "stop", CONTAINER], capture_output=True)

        self.stdout.write(f"restored {dump.name} into a clean container in {elapsed:.1f} s; SELECT count(*) FROM rental -> {known}")
        live = row_counts(live_db())
        diff = sorted(t for t in live.keys() | restored.keys() if live.get(t) != restored.get(t))
        if diff:
            self.stdout.write(f"tables that differ from {live_db()} (changed since the backup?): {', '.join(diff)}")
        else:
            self.stdout.write(f"all {len(live)} tables have the same row count as {live_db()}")
