from decimal import Decimal

from django.db import transaction
from django.db.models import F

from demo.models import Account


class InsufficientFunds(Exception):
    pass


def naive(account_id: int, amount: Decimal) -> Decimal:
    """Read, compute in Python, write. Two requests can read the same balance,
    and the second write overwrites the first: a lost update."""
    account = Account.objects.get(pk=account_id)
    if account.balance < amount:
        raise InsufficientFunds
    account.balance = account.balance - amount  # computed in Python
    account.save(update_fields=["balance"])  # UPDATE account SET balance = 90 WHERE id = 1
    return account.balance


def atomic(account_id: int, amount: Decimal) -> Decimal:
    """Fix 1: read and write in one statement and check the row count.
    UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10"""
    updated = Account.objects.filter(pk=account_id, balance__gte=amount).update(balance=F("balance") - amount)
    if updated == 0:
        Account.objects.get(pk=account_id)  # raises DoesNotExist if the account is missing
        raise InsufficientFunds
    return Account.objects.get(pk=account_id).balance


def lock(account_id: int, amount: Decimal) -> Decimal:
    """Fix 2: SELECT ... FOR UPDATE. A second request waits at the SELECT until
    the first one commits, then reads the new balance."""
    with transaction.atomic():
        account = Account.objects.select_for_update().get(pk=account_id)
        if account.balance < amount:
            raise InsufficientFunds
        account.balance = account.balance - amount
        account.save(update_fields=["balance"])
    return account.balance


STRATEGIES = {"naive": naive, "atomic": atomic, "lock": lock}
