"""customer:{id}:films in Redis, derived from the rentals in PostgreSQL (session 16)."""

from itertools import groupby

from django.db.models import Count

from demo.clients import r
from demo.models import Customer, Rental


def films_key(customer_id: int) -> str:
    return f"customer:{customer_id}:films"


def rebuild() -> int:
    """Every set from one query and one pipeline, each built in a temporary key and renamed."""
    pairs = (
        Rental.objects
        .values_list("customer_id", "inventory__film_id")
        .distinct()
        .order_by("customer_id")
    )
    customers = set(Customer.objects.values_list("customer_id", flat=True))
    pipe = r.pipeline(transaction=False)
    seen = set()
    for customer_id, rows in groupby(pairs.iterator(), key=lambda row: row[0]):
        key = films_key(customer_id)
        pipe.delete(key + ":rebuild")
        pipe.sadd(key + ":rebuild", *(film_id for _, film_id in rows))
        pipe.rename(key + ":rebuild", key)
        seen.add(customer_id)
    for customer_id in customers - seen:
        pipe.delete(films_key(customer_id))
    pipe.execute()
    return len(customers)


def verify() -> tuple[int, list[str]]:
    expected = list(
        Rental.objects
        .values("customer_id")
        .annotate(films=Count("inventory__film_id", distinct=True))
        .order_by("customer_id")
    )
    pipe = r.pipeline(transaction=False)
    for row in expected:
        pipe.scard(films_key(row["customer_id"]))
    errors = [
        f"customer {row['customer_id']}: redis={size} postgres={row['films']}"
        for row, size in zip(expected, pipe.execute())
        if size != row["films"]
    ]
    return len(expected), errors
