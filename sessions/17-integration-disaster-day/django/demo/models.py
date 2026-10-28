from django.db import models
from django.db.models import Q


class Account(models.Model):
    """The session 08 account, created by this project's migration."""

    id = models.IntegerField(primary_key=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "account"
        constraints = [
            # The last line of defence: even a buggy withdrawal cannot go below zero.
            models.CheckConstraint(condition=Q(balance__gte=0), name="account_balance_non_negative"),
        ]


# Pagila tables, managed = False: the rentals are written here, the rest is read.


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
    rental_date = models.DateTimeField()
    inventory = models.ForeignKey(Inventory, on_delete=models.DO_NOTHING, db_column="inventory_id")
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column="customer_id")
    staff_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "rental"


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "staff"


class Payment(models.Model):
    pk = models.CompositePrimaryKey("payment_date", "payment_id")
    payment_id = models.IntegerField()
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, db_column="staff_id")

    class Meta:
        managed = False
        db_table = "payment"
