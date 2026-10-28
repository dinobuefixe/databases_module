from django.db import models
from django.db.models import Q


class Account(models.Model):
    # CREATE TABLE account (id int PRIMARY KEY, balance numeric NOT NULL CHECK (balance >= 0))
    id = models.IntegerField(primary_key=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "account"
        constraints = [
            # The last line of defence: whatever the code does, the balance never goes negative.
            models.CheckConstraint(condition=Q(balance__gte=0), name="account_balance_not_negative"),
        ]
