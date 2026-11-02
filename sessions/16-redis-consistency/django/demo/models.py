from django.db import models

# PostgreSQL is the source of truth. These Pagila tables are only read.


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
