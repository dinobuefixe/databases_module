from django.db import models
from django.db.models.functions import Now

# Pagila tables: managed = False, so Django reads and writes them but its
# migrations never create, change or drop them. Only the columns we use are listed.


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.TextField()
    length = models.SmallIntegerField(null=True)
    rating = models.TextField(null=True)  # a PostgreSQL enum (mpaa_rating); text is enough to read and filter it
    rental_rate = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        managed = False
        db_table = "film"


class Actor(models.Model):
    actor_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()
    # db_default: Django leaves the value to the column default and reads it
    # back with RETURNING, together with the generated actor_id.
    last_update = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = "actor"


# New tables, created by this app's migrations.


class FilmViews(models.Model):
    film = models.OneToOneField(Film, primary_key=True, on_delete=models.DO_NOTHING, db_column="film_id")
    views = models.IntegerField(db_default=0)

    class Meta:
        db_table = "film_views"


class Person(models.Model):
    """Target of the bulk load command."""

    name = models.TextField()
    email = models.TextField()
    city = models.TextField()

    class Meta:
        db_table = "person"
