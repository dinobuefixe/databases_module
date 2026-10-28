import json
from decimal import Decimal, InvalidOperation

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from demo import derived
from demo.clients import mongo_db, r
from demo.models import Account, Inventory, Rental
from demo.reports import ReportExists, build_monthly_report, freeze_monthly_report, month_bounds


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body, parse_float=Decimal)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def check(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as exc:  # report any failure instead of crashing the health check
        return f"error: {exc}"


def ping_postgres() -> None:
    with connection.cursor() as cur:
        cur.execute("SELECT 1")


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    result = {"postgres": check(ping_postgres), "mongo": check(lambda: mongo_db.command("ping")), "redis": check(r.ping)}
    return JsonResponse(result, status=200 if all(v == "ok" for v in result.values()) else 503)


# --- PostgreSQL: the account withdrawal from session 08 --------------------------------


@require_GET
def account(request: HttpRequest, account_id: int) -> JsonResponse:
    acc = Account.objects.filter(pk=account_id).first()
    if acc is None:
        return JsonResponse({"error": "Account not found"}, status=404)
    return JsonResponse({"id": acc.id, "balance": str(acc.balance)})


@require_POST
def withdraw(request: HttpRequest, account_id: int) -> JsonResponse:
    body = read_json(request) or {}
    try:
        amount = Decimal(str(body.get("amount")))
    except InvalidOperation:
        amount = Decimal(0)
    if not amount.is_finite() or amount <= 0:
        return JsonResponse({"error": "amount must be a number greater than 0"}, status=422)

    # One atomic conditional UPDATE: read and write happen in the same statement.
    updated = Account.objects.filter(pk=account_id, balance__gte=amount).update(balance=F("balance") - amount)
    if updated == 0:
        if not Account.objects.filter(pk=account_id).exists():
            return JsonResponse({"error": "Account not found"}, status=404)
        return JsonResponse({"error": "Insufficient balance"}, status=409)
    return JsonResponse({"id": account_id, "withdrawn": str(amount)})


# --- PostgreSQL first, then Redis: a rental and the derived set from session 16 --------


@require_POST
def create_rental(request: HttpRequest) -> JsonResponse:
    body = read_json(request) or {}
    fields = ("customer_id", "inventory_id", "staff_id")
    if not all(isinstance(body.get(f), int) for f in fields):
        return JsonResponse({"error": f"{', '.join(fields)} are required integers"}, status=422)

    try:
        with transaction.atomic():
            inventory = Inventory.objects.filter(pk=body["inventory_id"]).first()
            if inventory is None:
                return JsonResponse({"error": "Inventory item not found"}, status=404)
            rental = Rental.objects.create(
                rental_date=timezone.now(),
                inventory_id=inventory.inventory_id,
                customer_id=body["customer_id"],
                staff_id=body["staff_id"],
            )
            # Redis is updated only after PostgreSQL commits. If the transaction rolls
            # back, Redis never hears of it. If Redis is down, robust=True logs the
            # error and the request still succeeds; verify and rebuild repair the set.
            transaction.on_commit(
                lambda: derived.add_film(body["customer_id"], inventory.film_id), robust=True
            )
    except IntegrityError as exc:  # unknown customer or staff: a foreign key says no
        return JsonResponse({"error": str(exc).splitlines()[0]}, status=422)

    return JsonResponse(
        {"rental_id": rental.rental_id, "customer_id": body["customer_id"], "film_id": inventory.film_id},
        status=201,
    )


@require_GET
def customer_films(request: HttpRequest, customer_id: int) -> JsonResponse:
    films = sorted(int(f) for f in r.smembers(derived.films_key(customer_id)))
    return JsonResponse({"customer_id": customer_id, "films": len(films), "film_ids": films})


@require_GET
def verify_view(request: HttpRequest) -> JsonResponse:
    checked, errors = derived.verify()
    return JsonResponse(
        {"ok": not errors, "checked": checked, "mismatches": len(errors), "first_mismatches": errors[:10]},
        status=200 if not errors else 503,
    )


# --- MongoDB: the frozen monthly report from session 14 --------------------------------


@require_http_methods(["GET", "POST"])
def monthly_report(request: HttpRequest, month: str) -> JsonResponse:
    try:
        month_bounds(month)
    except ValueError:
        return JsonResponse({"error": f"{month} is not a valid month"}, status=422)

    if request.method == "GET":
        report = mongo_db.monthly_reports.find_one({"_id": month})
        if report is None:
            return JsonResponse({"error": f"Report {month} has not been generated"}, status=404)
        return JsonResponse(report, encoder=DjangoJSONEncoder)

    report = build_monthly_report(month)
    if not report["stores"]:
        return JsonResponse({"error": f"No payments in {month}"}, status=422)
    try:
        freeze_monthly_report(report)
    except ReportExists:
        return JsonResponse({"error": f"Report {month} already exists and is frozen"}, status=409)
    return JsonResponse({"_id": month, "stores": len(report["stores"])}, status=201)
