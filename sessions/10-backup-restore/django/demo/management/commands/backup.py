from django.core.management.base import BaseCommand

from demo.pg import BACKUP_DIR, PG_USER, compose_exec, live_db, timestamp


class Command(BaseCommand):
    help = "pg_dump -Fc of this project's database and pg_dumpall --roles-only, into backups/."

    def handle(self, *args, **options):
        BACKUP_DIR.mkdir(exist_ok=True)
        stamp = timestamp()

        dump = BACKUP_DIR / f"{live_db()}_{stamp}.dump"
        with dump.open("wb") as out:
            compose_exec("pg_dump", "-U", PG_USER, "-Fc", live_db(), stdout=out)

        # pg_dump does not include roles; they belong to the whole server.
        roles = BACKUP_DIR / f"roles_{stamp}.sql"
        with roles.open("wb") as out:
            compose_exec("pg_dumpall", "-U", PG_USER, "--roles-only", stdout=out)

        for path in (dump, roles):
            self.stdout.write(f"{path.relative_to(BACKUP_DIR.parent)}  {path.stat().st_size / 1_048_576:.1f} MB")
