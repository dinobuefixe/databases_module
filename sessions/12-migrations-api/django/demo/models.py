from django.db import models


class Customer(models.Model):
    """The Pagila customer table, now managed by Django migrations.

    Only the columns this example uses are mapped. Django ignores the others
    (activebool, create_date, last_update, uuid) and never touches them.
    """

    customer_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField(null=True)
    active = models.IntegerField(null=True)
    # Migration 0002. db_default puts DEFAULT 0 in the table itself, so rows that
    # already exist get 0 and inserts from outside Django get it too.
    balance = models.DecimalField(max_digits=10, decimal_places=2, db_default=0)
    # Migrations 0003 to 0005: added as nullable, backfilled from active, then NOT NULL.
    tier = models.TextField()

    class Meta:
        db_table = "customer"
