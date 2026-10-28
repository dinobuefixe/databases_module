from pathlib import Path

from django.db import connection
from django.db.models import Avg, Count, DecimalField, Exists, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from demo.models import Customer, Film, Inventory, Payment, Rental

SQL_DIR = Path(__file__).parent / "sql"


# ORM versions. Each returns a list of dicts with the same keys as the SQL version.


def staff_rentals_orm() -> list[dict]:
    # values() before annotate() sets the GROUP BY. Grouping by staff_id as in the
    # SQL; Django reaches store_id through staff, so it does not join store.
    rows = (
        Rental.objects.values("staff_id")
        .annotate(
            store_id=F("staff__store_id"),
            first_name=F("staff__first_name"),
            last_name=F("staff__last_name"),
            rentals=Count("*"),
        )
        .order_by("store_id", "-rentals")
    )
    return [{k: row[k] for k in ("store_id", "first_name", "last_name", "rentals")} for row in rows]


def frequent_customers_orm() -> list[dict]:
    # filter() on an annotation that holds an aggregate becomes HAVING.
    return list(
        Customer.objects.annotate(rentals=Count("rental"))
        .filter(rentals__gt=40)
        .order_by("-rentals")
        .values("customer_id", "first_name", "last_name", "rentals")
    )


def rentals_per_customer_orm() -> list[dict]:
    # A reverse relation in annotate() is a LEFT OUTER JOIN. Count("rental") counts
    # rental.rental_id, which is NULL for a customer with no rentals; Count("*") counts rows.
    return list(
        Customer.objects.annotate(rentals=Count("rental"), joined_rows=Count("*"))
        .order_by("rentals", "customer_id")
        .values("customer_id", "first_name", "last_name", "rentals", "joined_rows")
    )


def films_without_inventory_orm() -> list[dict]:
    # ~Exists(...) with OuterRef is a correlated NOT EXISTS subquery.
    has_copy = Inventory.objects.filter(film_id=OuterRef("film_id"))
    return list(Film.objects.filter(~Exists(has_copy)).values("film_id", "title"))


def customers_without_rentals_orm() -> list[dict]:
    # rental__isnull=True on a reverse relation is the LEFT JOIN ... IS NULL anti-join.
    return list(
        Customer.objects.filter(rental__isnull=True)
        .order_by("customer_id")
        .values("customer_id", "first_name", "last_name")
    )


def duplicate_customer_names_orm() -> list[dict]:
    # The ORM joins a model to itself only along a foreign key, and customer has none to
    # customer. Closest form: one query for the customers that have a namesake (a correlated
    # EXISTS), then the pairs are built in Python.
    namesake = Customer.objects.filter(
        first_name=OuterRef("first_name"), last_name=OuterRef("last_name")
    ).exclude(customer_id=OuterRef("customer_id"))
    customers = list(
        Customer.objects.filter(Exists(namesake))
        .order_by("last_name", "first_name", "customer_id")
        .values("customer_id", "first_name", "last_name")
    )
    return [
        {
            "customer_id": a["customer_id"],
            "other_customer_id": b["customer_id"],
            "first_name": a["first_name"],
            "last_name": a["last_name"],
        }
        for i, a in enumerate(customers)
        for b in customers[i + 1 :]
        if (a["first_name"], a["last_name"]) == (b["first_name"], b["last_name"])
    ]


def films_longer_than_average_orm() -> list[dict]:
    # aggregate() runs at once and returns a number, so this is two queries;
    # the SQL version keeps the average as a subquery inside one statement.
    # Value() matters: a plain number is cast to the column type, so 115.27 would
    # be sent as the smallint 115.
    avg_length = Film.objects.aggregate(avg_length=Avg("length"))["avg_length"]
    return list(
        Film.objects.filter(length__gt=Value(avg_length))
        .order_by("-length", "film_id")
        .values("film_id", "title", "length")
    )


def films_above_rating_average_orm() -> list[dict]:
    # Subquery + OuterRef is a correlated subquery. values("rating") before annotate()
    # groups the inner query by rating; OuterRef ties it to the film being checked.
    rating_avg = (
        Film.objects.filter(rating=OuterRef("rating"))
        .values("rating")
        .annotate(avg_length=Avg("length"))
        .values("avg_length")
    )
    return list(
        Film.objects.filter(length__gt=Subquery(rating_avg))
        .order_by("rating", "-length", "film_id")
        .values("film_id", "title", "rating", "length")
    )


def customer_totals_orm() -> list[dict]:
    # Count("rental") and Sum("payment__amount") in one annotate() would join both
    # tables to customer at once and multiply the rows (see the README). Each total
    # is a correlated subquery instead; Django writes them in SELECT, not in FROM.
    rentals = (
        Rental.objects.filter(customer_id=OuterRef("customer_id"))
        .values("customer_id")
        .annotate(n=Count("*"))
        .values("n")
    )
    paid = (
        Payment.objects.filter(customer_id=OuterRef("customer_id"))
        .values("customer_id")
        .annotate(total=Sum("amount"))
        .values("total")
    )
    money = DecimalField(max_digits=10, decimal_places=2)
    return list(
        Customer.objects.annotate(
            rentals=Coalesce(Subquery(rentals), 0),
            paid=Coalesce(Subquery(paid, output_field=money), Value(0), output_field=money),
        )
        .order_by("customer_id")
        .values("customer_id", "first_name", "last_name", "rentals", "paid")
    )


def above_average_spenders_orm() -> list[dict]:
    # Django has no CTEs. Step 1 (spend) and step 2 (average) become one query
    # that returns a number; step 3 sends it back as a parameter.
    spend = Payment.objects.values("customer_id").annotate(total=Sum("amount"))
    avg_total = spend.aggregate(avg_total=Avg("total"))["avg_total"]
    return list(
        Customer.objects.annotate(total=Sum("payment__amount"))
        .filter(total__gt=avg_total)
        .order_by("-total")
        .values("first_name", "last_name", "total")
    )


ORM = {
    "staff-rentals": staff_rentals_orm,
    "frequent-customers": frequent_customers_orm,
    "rentals-per-customer": rentals_per_customer_orm,
    "films-without-inventory": films_without_inventory_orm,
    "customers-without-rentals": customers_without_rentals_orm,
    "duplicate-customer-names": duplicate_customer_names_orm,
    "films-longer-than-average": films_longer_than_average_orm,
    "films-above-rating-average": films_above_rating_average_orm,
    "customer-totals": customer_totals_orm,
    "above-average-spenders": above_average_spenders_orm,
}


def run_sql(name: str) -> list[dict]:
    """The tutorial's SQL, read from demo/sql/<name>.sql and run as it is."""
    sql = (SQL_DIR / f"{name.replace('-', '_')}.sql").read_text()
    with connection.cursor() as cur:
        cur.execute(sql)
        columns = [col.name for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def run(name: str, impl: str) -> list[dict]:
    return ORM[name]() if impl == "orm" else run_sql(name)
