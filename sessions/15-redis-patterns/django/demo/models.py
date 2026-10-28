from django.db import models


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.TextField()
    rental_rate = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = "film"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = "customer"
