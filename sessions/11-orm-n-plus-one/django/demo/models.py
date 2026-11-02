from django.db import models

# Two Pagila tables mapped as unmanaged models: Django reads and writes the rows
# but never creates, alters or drops the tables (managed = False).


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = "customer"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    rental_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True)
    # SQLAlchemy needs two attributes (customer_id and the relationship);
    # Django uses one ForeignKey, stored in the column customer_id.
    # related_name="rentals" gives customer.rentals, like back_populates.
    customer = models.ForeignKey(
        Customer, on_delete=models.DO_NOTHING, related_name="rentals", db_column="customer_id"
    )

    class Meta:
        managed = False
        db_table = "rental"
