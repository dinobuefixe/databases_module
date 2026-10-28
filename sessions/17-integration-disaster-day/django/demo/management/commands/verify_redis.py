import sys

from django.core.management.base import BaseCommand

from demo.derived import verify


class Command(BaseCommand):
    help = "Compares the Redis sets with PostgreSQL. Exit code 0 if they match, 1 if not."

    def handle(self, *args, **options):
        checked, errors = verify()
        for line in errors[:20]:
            self.stderr.write(line)
        if errors:
            self.stderr.write(self.style.ERROR(f"redis: {len(errors)} of {checked} customers differ"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS(f"redis: all {checked} customers match PostgreSQL"))
