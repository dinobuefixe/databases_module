from django.db import models

# Pagila's customer table. managed = False and no migrations in this project:
# the app role cannot create tables, and that is the point of this session.


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()
    first_name = models.TextField()
    last_name = models.TextField()
    email = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = "customer"
