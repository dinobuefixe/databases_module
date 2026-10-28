from collections import defaultdict

from bson import Decimal128
from django.core.management.base import BaseCommand
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from pymongo import ReplaceOne

from demo.clients import mongo_db
from demo.models import Customer, Film, FilmActor, FilmCategory, Rental

RECENT = 10


class Command(BaseCommand):
    help = "Builds the films and customers collections the session 14 pipelines read."

    def handle(self, *args, **options):
        self.load_films()
        self.load_customers()

    def load_films(self):
        actors = defaultdict(list)
        for film_id, actor_id, first, last in FilmActor.objects.values_list(
            "film_id", "actor_id", "actor__first_name", "actor__last_name"
        ):
            actors[film_id].append({"actor_id": actor_id, "name": f"{first} {last}"})
        categories = defaultdict(list)
        for film_id, name in FilmCategory.objects.order_by("film_id", "category__name").values_list(
            "film_id", "category__name"
        ):
            categories[film_id].append(name)

        ops = [
            ReplaceOne(
                {"_id": f["film_id"]},
                {
                    "title": f["title"],
                    "rating": f["rating"],
                    # Decimal128 keeps 0.99 exact; a float would store 0.98999...
                    "rental_rate": Decimal128(f["rental_rate"]),
                    "length": f["length"],
                    # Embedded: 1 to 3 names, read with the film.
                    "categories": categories[f["film_id"]],
                    "actors": actors[f["film_id"]],  # embedded: a film has a bounded cast
                },
                upsert=True,
            )
            for f in Film.objects.values("film_id", "title", "rating", "rental_rate", "length")
        ]
        mongo_db.films.bulk_write(ops)
        self.stdout.write(self.style.SUCCESS(f"films: {len(ops)} documents"))

    def load_customers(self):
        # The last 10 rentals of every customer in one query: number each customer's
        # rentals from newest to oldest with ROW_NUMBER() and keep numbers 1 to 10.
        recent = (
            Rental.objects.annotate(
                n=Window(RowNumber(), partition_by=F("customer_id"), order_by=F("rental_date").desc())
            )
            .filter(n__lte=RECENT)
            .values("customer_id", "rental_id", "rental_date", "inventory__film_id", "inventory__film__title")
        )
        rentals = defaultdict(list)
        for r in recent:
            rentals[r["customer_id"]].append(
                {
                    "rental_id": r["rental_id"],
                    "rental_date": r["rental_date"],
                    "film_id": r["inventory__film_id"],
                    "title": r["inventory__film__title"],
                }
            )

        ops = [
            ReplaceOne(
                {"_id": c["customer_id"]},
                {
                    "name": f"{c['first_name']} {c['last_name']}",
                    "store_id": c["store_id"],
                    "rentals_total": c["rentals_total"],
                    # Embedded: only the latest rentals. The full history grows without
                    # limit, so it stays in PostgreSQL and is referenced by customer_id.
                    "recent_rentals": rentals[c["customer_id"]],
                },
                upsert=True,
            )
            for c in Customer.objects.annotate(rentals_total=Count("rental")).values(
                "customer_id", "first_name", "last_name", "store_id", "rentals_total"
            )
        ]
        mongo_db.customers.bulk_write(ops)
        # Multikey index: one entry per embedded rental. A $match on the rental date at the
        # start of a pipeline can use it (see pipelines.match_position).
        mongo_db.customers.create_index("recent_rentals.rental_date")
        self.stdout.write(self.style.SUCCESS(f"customers: {len(ops)} documents"))
