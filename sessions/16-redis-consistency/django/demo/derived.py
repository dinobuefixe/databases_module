"""customer:{id}:films, a Redis set derived from PostgreSQL: rebuild and verify."""

from itertools import groupby

from demo.clients import r
from demo.models import Customer, Rental


def films_key(customer_id: int) -> str:
    return f"customer:{customer_id}:films"


def rebuild_customer(customer_id: int) -> None:
    """The tutorial's version: one query per customer, written to a temporary key and renamed."""
    key = films_key(customer_id)
    tmp = key + ":rebuild"
    film_ids = list(
        Rental.objects.using("readonly")
        .filter(customer_id=customer_id)
        .values_list("inventory__film_id", flat=True)
        .distinct()
    )

    pipe = r.pipeline(transaction=True)  # MULTI ... EXEC
    pipe.delete(tmp)
    if film_ids:
        pipe.sadd(tmp, *film_ids)
        pipe.rename(tmp, key)  # readers see the old set or the new one, never half of it
    else:
        pipe.delete(key)
    pipe.execute()


def rebuild_per_customer() -> int:
    ids = list(Customer.objects.using("readonly").order_by("customer_id").values_list("customer_id", flat=True))
    for customer_id in ids:
        rebuild_customer(customer_id)
    return len(ids)


def rebuild_single_query() -> int:
    """All rentals in one query, all sets in one pipeline (one round trip)."""
    pairs = (
        Rental.objects.using("readonly")
        .values_list("customer_id", "inventory__film_id")
        .distinct()
        .order_by("customer_id")
    )
    customers = set(Customer.objects.using("readonly").values_list("customer_id", flat=True))

    pipe = r.pipeline(transaction=False)
    seen = set()
    for customer_id, rows in groupby(pairs.iterator(), key=lambda row: row[0]):
        key, tmp = films_key(customer_id), films_key(customer_id) + ":rebuild"
        pipe.delete(tmp)
        pipe.sadd(tmp, *(film_id for _, film_id in rows))
        pipe.rename(tmp, key)
        seen.add(customer_id)
    for customer_id in customers - seen:  # customers with no rentals have no set
        pipe.delete(films_key(customer_id))
    pipe.execute()
    return len(customers)


def _ids(members: set[str]) -> str:
    """Film ids in numeric order ("9" before "10"), at most five of them."""
    ordered = sorted(members, key=lambda m: (len(m), m))
    shown = ", ".join(ordered[:5])
    return shown if len(ordered) <= 5 else f"{shown} ... ({len(ordered)} in total)"


def verify() -> tuple[int, list[str]]:
    """Compares the members of every set with PostgreSQL and looks for keys no customer
    explains. Returns (customers checked, mismatches)."""
    # Every customer gets an entry, so a customer with no rentals expects an empty set.
    # Redis returns members as strings, so compare strings.
    expected = {
        films_key(customer_id): set()
        for customer_id in Customer.objects.using("readonly").values_list("customer_id", flat=True)
    }
    pairs = Rental.objects.using("readonly").values_list("customer_id", "inventory__film_id").distinct()
    for customer_id, film_id in pairs.iterator():
        expected[films_key(customer_id)].add(str(film_id))

    pipe = r.pipeline(transaction=False)
    for key in expected:
        pipe.smembers(key)
    actual = pipe.execute()  # one round trip for all SMEMBERS calls

    errors = []
    for (key, want), have in zip(expected.items(), actual):
        if have != want:
            parts = []
            if want - have:
                parts.append(f"missing {_ids(want - have)}")
            if have - want:
                parts.append(f"extra {_ids(have - want)}")
            errors.append(f"{key}: {'; '.join(parts)}")

    # A set for a customer PostgreSQL does not have is also wrong. SCAN walks the
    # keys in batches; KEYS would block Redis while it runs.
    for key in r.scan_iter(match=films_key("*"), count=1000):
        if key not in expected:
            errors.append(f"{key}: no such customer in PostgreSQL ({r.scard(key)} members)")
    return len(expected), errors
