import json
from decimal import Decimal, InvalidOperation

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from demo.models import Account
from demo.withdraw import STRATEGIES, InsufficientFunds


def read_json(request: HttpRequest) -> dict:
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return {}
    return body if isinstance(body, dict) else {}


def account_list() -> JsonResponse:
    return JsonResponse({"accounts": list(Account.objects.order_by("id").values("id", "balance"))})


@require_GET
def accounts(request: HttpRequest) -> JsonResponse:
    return account_list()


@require_POST
def reset(request: HttpRequest) -> JsonResponse:
    """Accounts 1 and 2 back to the same balance (100 unless the body says otherwise)."""
    try:
        balance = Decimal(str(read_json(request).get("balance", 100)))
    except InvalidOperation:
        return JsonResponse({"error": "balance must be a number"}, status=400)
    Account.objects.bulk_create(
        [Account(id=1, balance=balance), Account(id=2, balance=balance)],
        update_conflicts=True, unique_fields=["id"], update_fields=["balance"],
    )
    return account_list()


@require_POST
def withdraw(request: HttpRequest, account_id: int) -> JsonResponse:
    """POST /accounts/<id>/withdraw?strategy=naive|atomic|lock  {"amount": 10}"""
    strategy = request.GET.get("strategy", "atomic")
    if strategy not in STRATEGIES:
        return JsonResponse({"error": f"strategy must be one of {list(STRATEGIES)}"}, status=400)
    try:
        amount = Decimal(str(read_json(request).get("amount", 10)))
    except InvalidOperation:
        return JsonResponse({"error": "amount must be a number"}, status=400)
    if amount <= 0:
        return JsonResponse({"error": "amount must be positive"}, status=400)

    try:
        balance = STRATEGIES[strategy](account_id, amount)
    except Account.DoesNotExist:
        return JsonResponse({"error": "account not found"}, status=404)
    except InsufficientFunds:
        return JsonResponse({"error": "insufficient funds"}, status=409)
    return JsonResponse({"account": account_id, "strategy": strategy, "balance": balance})
