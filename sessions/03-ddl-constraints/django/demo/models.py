from django.db import models
from django.db.models import Q
from django.db.models.functions import Now

# The tutorial's DDL as Django models. Every rule below ends up in the database
# (check with: uv run python manage.py sqlmigrate demo 0001), so it holds for any
# client, not only for this app. Constraint names are chosen by us so that the
# errors are easy to read and to map to HTTP responses.


class Author(models.Model):
    id = models.AutoField(primary_key=True, db_column="author_id")
    name = models.TextField()
    email = models.TextField()
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "author"
        constraints = [
            models.UniqueConstraint(fields=["email"], name="author_email_unique"),
        ]


class Ingredient(models.Model):
    id = models.AutoField(primary_key=True, db_column="ingredient_id")
    name = models.TextField()
    kcal_per_100g = models.DecimalField(max_digits=6, decimal_places=1)

    class Meta:
        db_table = "ingredient"
        constraints = [
            models.UniqueConstraint(fields=["name"], name="ingredient_name_unique"),
            models.CheckConstraint(condition=Q(kcal_per_100g__gte=0), name="ingredient_kcal_not_negative"),
        ]


class Recipe(models.Model):
    id = models.AutoField(primary_key=True, db_column="recipe_id")
    # RESTRICT: an author with published recipes cannot be deleted by accident.
    # Django 6.1 has no DB_RESTRICT. DO_NOTHING means Django does not check
    # anything in Python and leaves the decision to the foreign key in the
    # database, which refuses the delete (NO ACTION). models.RESTRICT or PROTECT
    # would check in Python instead, and only for deletes made through Django.
    author = models.ForeignKey(Author, on_delete=models.DO_NOTHING)
    title = models.TextField()
    servings = models.IntegerField()
    published_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "recipe"
        constraints = [
            # One author cannot publish two recipes with the same title.
            models.UniqueConstraint(fields=["author", "title"], name="recipe_author_title_unique"),
            models.CheckConstraint(condition=Q(servings__range=(1, 50)), name="recipe_servings_1_to_50"),
        ]


class RecipeIngredient(models.Model):
    pk = models.CompositePrimaryKey("recipe_id", "ingredient_id")
    # CASCADE: the ingredient list means nothing without its recipe.
    # DB_CASCADE (new in Django 6.1) writes ON DELETE CASCADE into the foreign key,
    # so PostgreSQL deletes the lines, whoever deletes the recipe.
    recipe = models.ForeignKey(Recipe, on_delete=models.DB_CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.DO_NOTHING)
    grams = models.DecimalField(max_digits=7, decimal_places=1)

    class Meta:
        db_table = "recipe_ingredient"
        constraints = [
            models.CheckConstraint(condition=Q(grams__gt=0), name="recipe_ingredient_grams_positive"),
        ]
