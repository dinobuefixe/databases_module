import sys

from django.core.management.base import BaseCommand

from demo.counts import row_counts
from demo.pg import live_db, own


class Command(BaseCommand):
    help = "Compare the row count of every table in two databases; exit 1 on any difference."

    def add_arguments(self, parser):
        parser.add_argument("first", nargs="?", help="default: your database")
        parser.add_argument("second", nargs="?", help="default: <your database>_restored")

    def handle(self, *args, first, second, **options):
        first = own(first or live_db())
        second = own(second or f"{live_db()}_restored")
        a, b = row_counts(first), row_counts(second)

        mismatches = 0
        self.stdout.write(f"{'table':<20} {first:>22} {second:>22}")
        for table in sorted(a.keys() | b.keys()):
            ca, cb = a.get(table), b.get(table)
            mark = "" if ca == cb else "  <- MISMATCH"
            mismatches += ca != cb
            # Show only the interesting rows, plus a summary.
            if mark or options["verbosity"] > 1:
                self.stdout.write(f"{table:<20} {str(ca):>22} {str(cb):>22}{mark}")
        self.stdout.write(f"{len(a | b)} tables compared, {mismatches} mismatches (use -v 2 to list every table)")
        if mismatches:
            sys.exit(1)
