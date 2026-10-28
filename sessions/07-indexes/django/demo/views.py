import re
from datetime import timedelta

from django.db import connection, transaction
from django.db.models.functions import Lower
from django.http import HttpRequest, JsonResponse, QueryDict
from django.utils import timezone
from django.views.decorators.http import require_GET

from demo import indexes
from demo.models import BigRental, Customer

EMAIL = "mary.smith@sakilacustomer.org"


def customer_latest(params: QueryDict) -> str:
    # The last 10 rentals of one customer: filter on customer_id, sort on rented_at.
    qs = BigRental.objects.filter(customer_id=42).order_by("-rented_at")[:10]
    return qs.explain(analyze=True, buffers=True)


def open_rentals(params: QueryDict) -> str:
    # count(*) with a filter. QuerySet.explain() needs a queryset and .count()
    # runs straight away, so this one is plain SQL with a parameter.
    with connection.cursor() as cur:
        cur.execute(
            "EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < %s",
            [timezone.now() - timedelta(days=30)],
        )
        return "\n".join(row[0] for row in cur.fetchall())


def customer_email_lower(params: QueryDict) -> str:
    # alias() + Lower: WHERE lower(email) = '...', which matches the expression index.
    qs = Customer.objects.alias(email_lower=Lower("email")).filter(email_lower=EMAIL)
    return qs.explain(analyze=True, buffers=True)


def customer_email_iexact(params: QueryDict) -> str:
    # email__iexact is written as UPPER(email) = UPPER('...'): the lower() index cannot be used.
    qs = Customer.objects.filter(email__iexact=EMAIL)
    return qs.explain(analyze=True, buffers=True)


def recent_rentals(params: QueryDict) -> str:
    # Every rental of the last ?days= days (730 by default). With big_rental_rented in place,
    # a few days use the index; two years match most of the table and get a Seq Scan.
    since = timezone.now() - timedelta(days=int(params.get("days", 730)))
    qs = BigRental.objects.filter(rented_at__gt=since)
    return qs.explain(analyze=True, buffers=True)


QUERIES = {
    "customer-latest": customer_latest,
    "open-rentals": open_rentals,
    "customer-email": customer_email_lower,
    "customer-email-iexact": customer_email_iexact,
    "recent-rentals": recent_rentals,
}


@require_GET
def index_list(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"present": indexes.existing()})


@require_GET
def explain(request: HttpRequest, name: str) -> JsonResponse:
    """GET /explain/<name>: EXPLAIN (ANALYZE, BUFFERS) of one tutorial query.

    ?force_index=1 turns off sequential and bitmap scans for this query only,
    to time the index scan the planner rejected.
    """
    if name not in QUERIES:
        return JsonResponse({"error": f"use one of {list(QUERIES)}"}, status=404)
    force_index = request.GET.get("force_index") == "1"
    with transaction.atomic():
        if force_index:
            with connection.cursor() as cur:
                # SET LOCAL ends with the transaction, so other requests are not affected.
                cur.execute("SET LOCAL enable_seqscan = off")
                cur.execute("SET LOCAL enable_bitmapscan = off")
        plan = QUERIES[name](request.GET)
    match = re.search(r"Execution Time: ([\d.]+) ms", plan)
    return JsonResponse(
        {
            "query": name,
            "force_index": force_index,
            "indexes_present": indexes.existing(),
            "execution_ms": float(match.group(1)) if match else None,
            "plan": plan.splitlines(),
        }
    )
