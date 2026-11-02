import json
from decimal import Decimal, InvalidOperation

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from demo.clients import r
from demo.derived import films_key
from demo.models import Account
from demo.withdraw import withdraw_atomic


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    result = {}
    for name, fn in (("postgres", lambda: connection.cursor().execute("SELECT 1")), ("redis", r.ping)):
        try:
            fn()
            result[name] = "ok"
        except Exception as exc:  # report any failure instead of crashing the health check
            result[name] = f"error: {exc}"
    return JsonResponse(result, status=200 if all(v == "ok" for v in result.values()) else 503)


@require_GET
def account(request: HttpRequest, account_id: int) -> JsonResponse:
    acc = Account.objects.filter(pk=account_id).first()
    if acc is None:
        return JsonResponse({"error": "Account not found"}, status=404)
    return JsonResponse({"id": acc.id, "balance": str(acc.balance)})


@require_POST
def withdraw(request: HttpRequest, account_id: int) -> JsonResponse:
    try:
        amount = Decimal(str(json.loads(request.body)["amount"]))
    except (json.JSONDecodeError, KeyError, TypeError, InvalidOperation):
        amount = Decimal(0)
    if not amount.is_finite() or amount <= 0:
        return JsonResponse({"error": "amount must be a number greater than 0"}, status=422)
    if withdraw_atomic(account_id, amount):
        return JsonResponse({"id": account_id, "withdrawn": str(amount)})
    if not Account.objects.filter(pk=account_id).exists():
        return JsonResponse({"error": "Account not found"}, status=404)
    return JsonResponse({"error": "Insufficient balance"}, status=409)


@require_GET
def customer_films(request: HttpRequest, customer_id: int) -> JsonResponse:
    films = sorted(int(f) for f in r.smembers(films_key(customer_id)))
    return JsonResponse({"customer_id": customer_id, "films": len(films), "film_ids": films})
