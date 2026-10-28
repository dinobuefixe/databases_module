from django.db import models

# The recipe spreadsheet split into one table per entity. Each fact lives in the
# table it depends on: the email on the author, the calories on the ingredient,
# the grams on the recipe-ingredient pair.
# This session only declares primary keys, foreign keys and NOT NULL (Django
# columns are NOT NULL unless null=True). Session 03 adds CHECK and UNIQUE.


class Author(models.Model):
    id = models.AutoField(primary_key=True, db_column="author_id")
    name = models.TextField()
    email = models.TextField()

    class Meta:
        db_table = "author"


class Ingredient(models.Model):
    id = models.AutoField(primary_key=True, db_column="ingredient_id")
    name = models.TextField()
    kcal_per_100g = models.DecimalField(max_digits=6, decimal_places=1)

    class Meta:
        db_table = "ingredient"


class Recipe(models.Model):
    id = models.AutoField(primary_key=True, db_column="recipe_id")
    # on_delete here is Django behaviour in Python, not a database rule. Session 03
    # looks at what ends up in the database.
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    title = models.TextField()
    servings = models.IntegerField()
    # Deliberate denormalisation: the listing page reads this column instead of
    # summing the ingredients of every recipe. It is recalculated in the same
    # transaction whenever the ingredient list changes (see services.py).
    kcal_per_serving = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient")

    class Meta:
        db_table = "recipe"


class RecipeIngredient(models.Model):
    # N:N with its own data (grams), so it is a model of its own.
    # The primary key is the pair (recipe_id, ingredient_id), as in the ER diagram.
    pk = models.CompositePrimaryKey("recipe_id", "ingredient_id")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    grams = models.DecimalField(max_digits=7, decimal_places=1)

    class Meta:
        db_table = "recipe_ingredient"
