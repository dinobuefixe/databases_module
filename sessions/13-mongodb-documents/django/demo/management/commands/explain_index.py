from django.core.management.base import BaseCommand

from demo.clients import stores
from demo.documents import COUNTRY_INDEX, explain_find


class Command(BaseCommand):
    help = "explain('executionStats') for find by address.country, without and then with an index."

    def add_arguments(self, parser):
        parser.add_argument("--country", default="India")

    def handle(self, *args, country, **options):
        if COUNTRY_INDEX in stores.index_information():
            stores.drop_index(COUNTRY_INDEX)

        before = explain_find(country)
        stores.create_index("address.country")
        after = explain_find(country)

        for label, stats in (("before", before), ("after", after)):
            self.stdout.write(f"{label:>6}: {' <- '.join(stats['stages'])}")
            for key in ("nReturned", "totalDocsExamined", "totalKeysExamined", "executionTimeMillis"):
                self.stdout.write(f"        {key} = {stats[key]}")
