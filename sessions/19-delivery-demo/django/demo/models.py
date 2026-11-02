from django.db import models
from django.db.models import Q


class Account(models.Model):
    """Session 08: the balance can never go below zero, whatever the code does."""

    id = models.IntegerField(primary_key=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "account"
        constraints = [models.CheckConstraint(condition=Q(balance__gte=0), name="account_balance_non_negative")]


class BigRental(models.Model):
    """Session 07: created by setup_demo with CREATE TABLE AS, so Django does not manage it."""

    id = models.IntegerField(primary_key=True)
    customer_id = models.IntegerField()
    rented_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = "big_rental"


# The two indexes demo_explain creates and drops. Declared with Django's Index class
# and applied with the schema editor, so the demo controls when they exist.
BIG_RENTAL_INDEXES = [
    models.Index(fields=["customer_id", "-rented_at"], name="big_rental_customer_rented"),
    models.Index(fields=["rented_at"], name="big_rental_open", condition=Q(returned_at__isnull=True)),
]


# Pagila tables read by the Redis rebuild (session 16).


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = "customer"


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    film_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "inventory"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    inventory = models.ForeignKey(Inventory, on_delete=models.DO_NOTHING, db_column="inventory_id")
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column="customer_id")

    class Meta:
        managed = False
        db_table = "rental"
