import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from demo.models import Customer


def as_dict(c: Customer) -> dict:
    return {
        "customer_id": c.customer_id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "tier": c.tier,
        "balance": str(c.balance),
    }


def parse_amount(request: HttpRequest) -> Decimal | None:
    """What Pydantic's Field(gt=0) does in the FastAPI version: a positive number, at most 2 decimals."""
    try:
        amount = Decimal(str(json.loads(request.body)["amount"]))
    except (json.JSONDecodeError, KeyError, TypeError, InvalidOperation):
        return None
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        return None
    return amount


def invalid_amount() -> JsonResponse:
    return JsonResponse({"error": "amount must be a number greater than 0 with at most 2 decimals"}, status=422)


@require_GET
def customer_detail(request: HttpRequest, customer_id: int) -> JsonResponse:
    customer = Customer.objects.filter(pk=customer_id).first()
    if customer is None:
        return JsonResponse({"error": "Customer not found"}, status=404)
    return JsonResponse(as_dict(customer))


@require_POST
def charge(request: HttpRequest, customer_id: int) -> JsonResponse:
    amount = parse_amount(request)
    if amount is None:
        return invalid_amount()

    # transaction.atomic() is `with session.begin():` commit at the end, roll back on an exception.
    with transaction.atomic():
        # select_for_update() adds FOR UPDATE: a second charge for the same customer
        # waits here until this transaction ends, so both cannot read the same balance.
        customer = Customer.objects.select_for_update().filter(pk=customer_id).first()
        if customer is None:
            return JsonResponse({"error": "Customer not found"}, status=404)
        if customer.balance < amount:
            return JsonResponse({"error": "Insufficient balance", "balance": str(customer.balance)}, status=409)
        customer.balance -= amount
        customer.save(update_fields=["balance"])

    return JsonResponse({"customer_id": customer_id, "balance": str(customer.balance)})


@require_POST
def top_up(request: HttpRequest, customer_id: int) -> JsonResponse:
    """Adds to the balance so that the charge endpoint has something to take."""
    amount = parse_amount(request)
    if amount is None:
        return invalid_amount()

    with transaction.atomic():
        customer = Customer.objects.select_for_update().filter(pk=customer_id).first()
        if customer is None:
            return JsonResponse({"error": "Customer not found"}, status=404)
        customer.balance += amount
        customer.save(update_fields=["balance"])

    return JsonResponse({"customer_id": customer_id, "balance": str(customer.balance)})
