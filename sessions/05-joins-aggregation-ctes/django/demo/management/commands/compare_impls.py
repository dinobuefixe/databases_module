from django.core.management.base import BaseCommand, CommandError

from demo.queries import ORM, run


def key(row: dict) -> tuple:
    return tuple(str(v) for v in row.values())


class Command(BaseCommand):
    help = "Run every report with the ORM and with SQL and check they return the same rows."

    def handle(self, *args, **options):
        failed = []
        for name in ORM:
            orm_rows, sql_rows = run(name, "orm"), run(name, "sql")
            # Compare as sorted lists: ties in ORDER BY may come back in any order.
            same = sorted(map(key, orm_rows)) == sorted(map(key, sql_rows))
            self.stdout.write(f"{'same' if same else 'DIFFERENT':<10} {name}: orm {len(orm_rows)} rows, sql {len(sql_rows)} rows")
            if not same:
                failed.append(name)
        if failed:
            raise CommandError(f"different results: {', '.join(failed)}")
