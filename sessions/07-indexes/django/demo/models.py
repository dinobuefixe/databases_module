from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

# Both tables are managed = False: big_rental is created by the make_big_rental
# command (CREATE TABLE ... AS SELECT, which Django cannot express) and customer
# belongs to Pagila. The indexes are still declared here, the Django way, and the
# `index` command builds them from these definitions with the schema editor, so
# they can be created and dropped while you compare plans.


class BigRental(models.Model):
    id = models.IntegerField(primary_key=True)  # no real primary key: CREATE TABLE AS copies none
    customer_id = models.IntegerField()
    rented_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = "big_rental"
        indexes = [
            # Composite: equality column first, sort column second, in the order the query sorts.
            models.Index(fields=["customer_id", "-rented_at"], name="big_rental_customer_rented"),
            # Partial: only the ~3% of rows not yet returned.
            models.Index(fields=["rented_at"], condition=Q(returned_at__isnull=True), name="big_rental_open"),
            # Plain index on rented_at: used for the last few days, ignored for the last two years.
            models.Index(fields=["rented_at"], name="big_rental_rented"),
        ]


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    email = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = "customer"
        indexes = [
            # Expression index: lets WHERE lower(email) = ... use an index.
            models.Index(Lower("email"), name="customer_lower_email"),
        ]


TUTORIAL_INDEXES = {index.name: (model, index) for model in (BigRental, Customer) for index in model._meta.indexes}
