from django.db import models

# Pagila tables read by the loader and the monthly report (managed = False).


class Actor(models.Model):
    actor_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()

    class Meta:
        managed = False
        db_table = "actor"


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.TextField()
    rating = models.TextField(null=True)  # a PostgreSQL enum (mpaa_rating), read as text
    rental_rate = models.DecimalField(max_digits=4, decimal_places=2)
    length = models.SmallIntegerField(null=True)  # minutes

    class Meta:
        managed = False
        db_table = "film"


class FilmActor(models.Model):
    # film_actor has a two-column primary key; Django maps it with CompositePrimaryKey.
    pk = models.CompositePrimaryKey("actor_id", "film_id")
    actor = models.ForeignKey(Actor, on_delete=models.DO_NOTHING, db_column="actor_id")
    film = models.ForeignKey(Film, on_delete=models.DO_NOTHING, db_column="film_id")

    class Meta:
        managed = False
        db_table = "film_actor"


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = "category"


class FilmCategory(models.Model):
    # In this Pagila a film has 1 to 3 categories.
    pk = models.CompositePrimaryKey("film_id", "category_id")
    film = models.ForeignKey(Film, on_delete=models.DO_NOTHING, db_column="film_id")
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, db_column="category_id")

    class Meta:
        managed = False
        db_table = "film_category"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()
    first_name = models.TextField()
    last_name = models.TextField()

    class Meta:
        managed = False
        db_table = "customer"


class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    film = models.ForeignKey(Film, on_delete=models.DO_NOTHING, db_column="film_id")

    class Meta:
        managed = False
        db_table = "inventory"


class Rental(models.Model):
    rental_id = models.AutoField(primary_key=True)
    rental_date = models.DateTimeField()
    inventory = models.ForeignKey(Inventory, on_delete=models.DO_NOTHING, db_column="inventory_id")
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column="customer_id")

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
    # payment is partitioned by payment_date, which is part of its primary key.
    pk = models.CompositePrimaryKey("payment_date", "payment_id")
    payment_id = models.IntegerField()
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    staff = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, db_column="staff_id")

    class Meta:
        managed = False
        db_table = "payment"
