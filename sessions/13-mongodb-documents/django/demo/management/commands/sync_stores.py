from django.core.management.base import BaseCommand
from pymongo import UpdateOne

from demo.clients import stores
from demo.models import Store


class Command(BaseCommand):
    help = "Reads every Pagila store from PostgreSQL and upserts one document per store into MongoDB."

    def handle(self, *args, **options):
        # Two SQL queries: stores joined to address, city, country and manager,
        # then all staff for those stores (prefetch_related).
        qs = (
            Store.objects.select_related("address__city__country", "manager")
            .prefetch_related("staff")
            .order_by("store_id")
        )

        ops = []
        for s in qs:
            doc = {
                # Embedded: read with the store, owned by it, and bounded in size.
                "manager": {"staff_id": s.manager.staff_id, "name": s.manager.name},
                "address": {
                    "line": s.address.address,
                    "city": s.address.city.city,
                    "country": s.address.city.country.country,
                },
                "staff": [{"staff_id": st.staff_id, "name": st.name} for st in s.staff.all()],
            }
            # The store id from PostgreSQL becomes _id, so running the sync again
            # updates the same documents instead of adding new ones.
            ops.append(UpdateOne({"_id": s.store_id}, {"$set": doc}, upsert=True))

        # The tutorial calls update_one() in a loop: one round trip per store.
        # bulk_write() sends the same operations in batches.
        result = stores.bulk_write(ops, ordered=False)
        self.stdout.write(
            self.style.SUCCESS(
                f"{len(ops)} stores: {result.upserted_count} inserted, {result.modified_count} modified"
            )
        )
