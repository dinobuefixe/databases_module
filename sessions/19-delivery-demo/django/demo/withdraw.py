"""Three ways to take 10 from an account (session 08). Only the last two are safe."""

import time
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from demo.models import Account


def withdraw_naive(account_id: int, amount: Decimal) -> bool:
    """Read, compute in Python, write: two requests can read the same balance."""
    with transaction.atomic():
        acc = Account.objects.get(pk=account_id)
        if acc.balance < amount:
            return False
        time.sleep(0.01)  # stands in for the work a real request does between read and write
        acc.balance = acc.balance - amount
        acc.save(update_fields=["balance"])
    return True


def withdraw_atomic(account_id: int, amount: Decimal) -> bool:
    """UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10"""
    return Account.objects.filter(pk=account_id, balance__gte=amount).update(balance=F("balance") - amount) == 1


def withdraw_lock(account_id: int, amount: Decimal) -> bool:
    """SELECT ... FOR UPDATE: the second request waits until the first commits."""
    with transaction.atomic():
        acc = Account.objects.select_for_update().get(pk=account_id)
        if acc.balance < amount:
            return False
        time.sleep(0.01)
        acc.balance = acc.balance - amount
        acc.save(update_fields=["balance"])
    return True


STRATEGIES = {"naive": withdraw_naive, "atomic": withdraw_atomic, "lock": withdraw_lock}
