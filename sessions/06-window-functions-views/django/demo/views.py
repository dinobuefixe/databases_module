import time
from datetime import date

from django.db import OperationalError, connection
from django.db.models import F, Sum, Window
from django.db.models.functions import DenseRank, Lag
from django.http import HttpRequest, JsonResponse
from django.test.utils import CaptureQueriesContext
from django.views.decorators.http import require_GET, require_POST

from demo.models import DailyRental, Film, Payment, Rental


def with_sql(fn) -> dict:
    """Run fn and return its rows together with the SQL Django sent."""
    with CaptureQueriesContext(connection) as ctx:
        rows = fn()
    return {"count": len(rows), "sql": [q["sql"] for q in ctx.captured_queries], "rows": rows}


@require_GET
def longest_per_rating(request: HttpRequest) -> JsonResponse:
    """The N longest films per rating, ties sharing a position (DENSE_RANK)."""
    try:
        top = int(request.GET.get("top", 2))
    except ValueError:
        return JsonResponse({"error": "top must be an integer"}, status=400)

    def query():
        ranked = Film.objects.annotate(
            pos=Window(DenseRank(), partition_by="rating", order_by=F("length").desc())
        )
        # SQL cannot use a window function in WHERE. Django sees the filter on a
        # window annotation and wraps the query in a subquery, like the tutorial's CTE.
        return list(ranked.filter(pos__lte=top).order_by("rating", "pos", "title").values("title", "rating", "length", "pos"))

    return JsonResponse({"top": top, **with_sql(query)})


@require_GET
def running_total(request: HttpRequest, customer_id: int) -> JsonResponse:
    """Each payment of one customer with the total paid so far."""

    def query():
        return list(
            Payment.objects.filter(customer_id=customer_id)
            .annotate(running_total=Window(Sum("amount"), partition_by="customer_id", order_by="payment_date"))
            .order_by("payment_date")
            .values("payment_date", "amount", "running_total")
        )

    return JsonResponse({"customer_id": customer_id, **with_sql(query)})


@require_GET
def rental_gaps(request: HttpRequest, customer_id: int) -> JsonResponse:
    """Time since the customer's previous rental (LAG)."""

    def query():
        previous = Window(Lag("rental_date"), partition_by="customer_id", order_by="rental_date")
        return list(
            Rental.objects.filter(customer_id=customer_id)
            .annotate(gap=F("rental_date") - previous)
            .order_by("rental_date")
            .values("rental_date", "gap")  # gap is an ISO 8601 duration, null for the first rental
        )

    return JsonResponse({"customer_id": customer_id, **with_sql(query)})


@require_GET
def daily_rentals(request: HttpRequest) -> JsonResponse:
    """Read the materialised view: fast, but only as fresh as the last refresh."""
    try:
        start = date.fromisoformat(request.GET.get("from", "2022-01-01"))
        end = date.fromisoformat(request.GET.get("to", "9999-12-31"))
    except ValueError:
        return JsonResponse({"error": "from and to must be dates (YYYY-MM-DD)"}, status=400)

    def query():
        return list(DailyRental.objects.filter(day__range=(start, end)).order_by("day").values("day", "rentals"))

    return JsonResponse(with_sql(query))


@require_POST
def refresh_daily_rentals(request: HttpRequest) -> JsonResponse:
    """CONCURRENTLY: readers keep seeing the old rows while the new ones are computed."""
    started = time.perf_counter()
    try:
        with connection.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY daily_rentals")
    except OperationalError as exc:
        # For example when the unique index is missing: CONCURRENTLY needs it.
        return JsonResponse({"error": str(exc)}, status=409)
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    return JsonResponse({"refreshed": "daily_rentals", "ms": elapsed, "days": DailyRental.objects.count()})
