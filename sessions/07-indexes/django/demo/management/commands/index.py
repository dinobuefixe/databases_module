from django.core.management.base import BaseCommand, CommandError

from demo import indexes
from demo.models import TUTORIAL_INDEXES


class Command(BaseCommand):
    help = "Create or drop the tutorial indexes declared in Meta.indexes."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["create", "drop", "list"])
        parser.add_argument("name", nargs="?", default="all", help=f"one of {list(TUTORIAL_INDEXES)} or all")

    def handle(self, *args, action, name, **options):
        if action == "list":
            present = indexes.existing()
            for index in TUTORIAL_INDEXES:
                self.stdout.write(f"{'present' if index in present else 'absent ':<8} {index}")
            return

        names = list(TUTORIAL_INDEXES) if name == "all" else [name]
        if any(n not in TUTORIAL_INDEXES for n in names):
            raise CommandError(f"unknown index, use one of {list(TUTORIAL_INDEXES)} or all")
        present = indexes.existing()
        for n in names:
            if (action == "create") == (n in present):
                self.stdout.write(f"skip     {n} (already {'present' if n in present else 'absent'})")
                continue
            sql = indexes.create(n) if action == "create" else indexes.drop(n)
            self.stdout.write(sql)
