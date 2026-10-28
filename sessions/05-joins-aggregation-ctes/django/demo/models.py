from django.db import models

# Pagila tables used by the questions. managed = False: Django reads them
# but its migrations never touch them. Only the columns we need are listed.


class Store(models.Model):
    store_id = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = "store"


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "staff"


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
    length = models.SmallIntegerField(null=True)
    rating = models.TextField(null=True)  # a PostgreSQL enum (mpaa_rating), read as text

    class Meta:
        managed = False
        db_table = "film"


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    film = models.ForeignKey(Film, on_delete=models.DO_NOTHING)
    store = models.ForeignKey(Store, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "inventory"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING)
    inventory = models.ForeignKey(Inventory, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "rental"


class Payment(models.Model):
    # The real primary key is (payment_date, payment_id) because the table is
    # partitioned by date. payment_id alone is unique too, which is enough for reads.
    payment_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    payment_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "payment"
