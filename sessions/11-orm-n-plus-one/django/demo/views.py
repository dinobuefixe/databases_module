from django.db import connection
from django.db.models import FETCH_PEERS, Count
from django.http import HttpRequest, JsonResponse
from django.test.utils import CaptureQueriesContext
from django.views.decorators.http import require_GET

from demo.models import Customer, Rental


def parse_limit(request: HttpRequest, default: int) -> int:
    try:
        return max(1, min(int(request.GET.get("limit", default)), 100))
    except ValueError:
        return default


def parse_eager(request: HttpRequest) -> bool:
    return request.GET.get("eager", "false").lower() == "true"


def captured(ctx: CaptureQueriesContext) -> dict:
    """How many statements ran inside the block, and the first few of them."""
    return {
        "queries": len(ctx.captured_queries),
        "first_statements": [q["sql"] for q in ctx.captured_queries[:3]],
    }


@require_GET
def customers(request: HttpRequest) -> JsonResponse:
    """Customers with their number of rentals: 1 + N queries, or 2 with prefetch_related."""
    limit = parse_limit(request, 20)
    eager = parse_eager(request)

    with CaptureQueriesContext(connection) as ctx:
        qs = Customer.objects.order_by("customer_id")
        if eager:
            # selectinload in SQLAlchemy: a second query with WHERE customer_id IN (...)
            qs = qs.prefetch_related("rentals")
        data = [
            {
                "customer_id": c.customer_id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                # Without the prefetch, each .all() runs its own SELECT on rental.
                "rentals": len(c.rentals.all()),
            }
            for c in qs[:limit]
        ]

    return JsonResponse({"eager": eager, **captured(ctx), "customers": data})


@require_GET
def rentals(request: HttpRequest) -> JsonResponse:
    """The N:1 side: recent rentals with their customer's name.

    eager=true uses select_related (a JOIN). eager=peers uses a fetch mode
    (available in the installed Django 6.1): the first r.customer access loads
    the customer of every rental from the same queryset in one extra query.
    """
    limit = parse_limit(request, 20)
    eager = request.GET.get("eager", "false").lower()

    with CaptureQueriesContext(connection) as ctx:
        qs = Rental.objects.order_by("-rental_date")
        if eager == "true":
            # joinedload in SQLAlchemy: one query with a JOIN on customer
            qs = qs.select_related("customer")
        elif eager == "peers":
            qs = qs.fetch_mode(FETCH_PEERS)
        data = [
            {
                "rental_id": r.rental_id,
                "rental_date": r.rental_date,
                "customer": f"{r.customer.first_name} {r.customer.last_name}",
            }
            for r in qs[:limit]
        ]

    return JsonResponse({"eager": eager, **captured(ctx), "rentals": data})


@require_GET
def top_customers(request: HttpRequest) -> JsonResponse:
    """Top customers by number of rentals, aggregated in the database (GROUP BY)."""
    limit = parse_limit(request, 5)
    qs = (
        Customer.objects.annotate(n=Count("rentals"))
        .order_by("-n", "customer_id")
        .values("customer_id", "last_name", "n")[:limit]
    )
    with CaptureQueriesContext(connection) as ctx:
        data = list(qs)
    return JsonResponse({"sql": str(qs.query), "queries": len(ctx.captured_queries), "customers": data})
