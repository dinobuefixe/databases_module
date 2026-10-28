from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Film(models.Model):
    film_id = models.AutoField(primary_key=True)
    title = models.TextField()
    rating = models.TextField(null=True)

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


class FilmReview(models.Model):
    """A customer's review of a film. Stars go from 1 to 5."""

    film = models.ForeignKey(Film, on_delete=models.DO_NOTHING, related_name="reviews")
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, related_name="reviews")
    stars = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "film_review"
        indexes = [models.Index(fields=["comment"], name="film_review_comment_idx")]
