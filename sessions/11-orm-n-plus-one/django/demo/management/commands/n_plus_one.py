from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.test.utils import CaptureQueriesContext

from demo.models import Customer


class Command(BaseCommand):
    help = "The session 11 tutorial script: N+1, the prefetch fix and an aggregation, with query counts."

    def handle(self, *args, **options):
        # 1. N+1: one query for the customers, then one per customer
        with CaptureQueriesContext(connection) as ctx:
            for c in Customer.objects.order_by("customer_id")[:20]:
                self.stdout.write(f"{c.first_name} {len(c.rentals.all())}")
        self.stdout.write(self.style.WARNING(f"-> lazy loading: {len(ctx)} queries\n"))

        # 2. Fixed: two queries in total. Each QuerySet is new, so nothing is reused
        # from block 1 (Django has no identity map, unlike a SQLAlchemy Session).
        with CaptureQueriesContext(connection) as ctx:
            for c in Customer.objects.order_by("customer_id").prefetch_related("rentals")[:20]:
                self.stdout.write(f"{c.first_name} {len(c.rentals.all())}")
        self.stdout.write(self.style.SUCCESS(f"-> prefetch_related: {len(ctx)} queries\n"))

        # 3. Aggregation in the ORM: one query with JOIN and GROUP BY
        qs = Customer.objects.annotate(n=Count("rentals")).order_by("-n")[:5]
        with CaptureQueriesContext(connection) as ctx:
            for c in qs:
                self.stdout.write(f"{c.last_name} {c.n}")
        self.stdout.write(self.style.SUCCESS(f"-> annotate(Count): {len(ctx)} query"))
        self.stdout.write(str(qs.query))
