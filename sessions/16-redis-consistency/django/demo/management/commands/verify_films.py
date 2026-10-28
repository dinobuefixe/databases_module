import sys

from django.core.management.base import BaseCommand

from demo.derived import verify


class Command(BaseCommand):
    help = "Compares the Redis sets with PostgreSQL, members and orphan keys. Exit code 0 if they match, 1 if not (for CI or cron)."

    def handle(self, *args, **options):
        checked, errors = verify()
        for line in errors:
            self.stderr.write(line)
        if errors:
            self.stderr.write(self.style.ERROR(f"{len(errors)} keys differ ({checked} customers checked)"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS(f"All {checked} customers match"))
