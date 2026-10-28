import subprocess
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from demo.clients import container_mongo_url


class Command(BaseCommand):
    help = "mongodump of this project's MongoDB database into backups/, one gzipped archive."

    def handle(self, *args, **options):
        backups = settings.BASE_DIR / "backups"
        backups.mkdir(exist_ok=True)
        path = backups / f"mongo_{settings.MONGO_DB}_{datetime.now():%Y-%m-%d_%H%M%S}.archive.gz"
        # Write to a temporary name and rename only when mongodump succeeds. Otherwise a failed
        # dump leaves an empty .archive.gz behind, and mongo_restore picks it as the newest.
        part = path.with_name(path.name + ".part")

        # mongodump runs inside the mongo container (-T: no pseudo-terminal, so the
        # binary archive on stdout is not corrupted) and we write its output to a file.
        try:
            with part.open("wb") as out:
                subprocess.run(
                    ["docker", "compose", "exec", "-T", "mongo", "mongodump",
                     "--uri", container_mongo_url(), "--db", settings.MONGO_DB, "--archive", "--gzip"],
                    cwd=settings.REPO_ROOT, stdout=out, check=True,
                )
        except subprocess.CalledProcessError as e:
            part.unlink()
            raise CommandError(f"mongodump failed (exit {e.returncode}); no backup written") from None
        part.rename(path)
        self.stdout.write(self.style.SUCCESS(f"{path} ({path.stat().st_size:,} bytes)"))
