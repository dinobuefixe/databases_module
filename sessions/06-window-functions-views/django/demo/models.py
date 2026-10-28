from django.db import models

# Pagila tables (managed = False) with only the columns the queries use.


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()

    class Meta:
        managed = False
        db_table = "customer"


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.TextField()
    rating = models.TextField(null=True)
    length = models.SmallIntegerField(null=True)

    class Meta:
        managed = False
        db_table = "film"


class Payment(models.Model):
    # Real primary key: (payment_date, payment_id). payment_id is unique on its own.
    payment_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    payment_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payment"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    rental_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "rental"


class DailyRental(models.Model):
    """The materialised view daily_rentals, read like a table.

    managed = False because Django cannot create a materialised view; migration
    0002 creates it with RunSQL.
    """

    day = models.DateField(primary_key=True)
    rentals = models.IntegerField()

    class Meta:
        managed = False
        db_table = "daily_rentals"
