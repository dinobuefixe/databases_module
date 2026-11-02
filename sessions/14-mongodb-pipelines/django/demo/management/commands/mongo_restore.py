import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from demo.clients import container_mongo_url, mongo


class Command(BaseCommand):
    help = "Restores an archive into <MONGO_DB>_restored and compares document counts with the original."

    def add_arguments(self, parser):
        parser.add_argument("archive", nargs="?", help="defaults to the newest file in backups/")

    def handle(self, *args, archive, **options):
        if archive is None:
            archives = sorted((settings.BASE_DIR / "backups").glob("mongo_*.archive.gz"))
            if not archives:
                raise CommandError("No archive in backups/. Run mongo_backup first.")
            archive = archives[-1]
        source = settings.MONGO_DB
        target = f"{source}_restored"

        # --nsInclude reads only our database from the archive and --nsFrom/--nsTo
        # renames it on the way in, so --drop only replaces collections in the target.
        with Path(archive).open("rb") as inp:
            subprocess.run(
                ["docker", "compose", "exec", "-T", "mongo", "mongorestore",
                 "--uri", container_mongo_url(), "--archive", "--gzip", "--drop",
                 "--nsInclude", f"{source}.*", "--nsFrom", f"{source}.*", "--nsTo", f"{target}.*"],
                cwd=settings.REPO_ROOT, stdin=inp, check=True,
            )

        mismatches = 0
        for name in sorted(mongo[source].list_collection_names()):
            before = mongo[source][name].count_documents({})
            after = mongo[target][name].count_documents({})
            mismatches += before != after
            self.stdout.write(f"{name:<18} {source}={before:<6} {target}={after}")
        if mismatches:
            raise CommandError(f"{mismatches} collection(s) differ", returncode=1)
        self.stdout.write(self.style.SUCCESS(f"Restored {archive} into {target}"))
