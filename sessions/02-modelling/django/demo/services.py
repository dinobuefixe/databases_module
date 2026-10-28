from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum

from demo.models import Recipe, RecipeIngredient


def recalculate_kcal(recipe: Recipe) -> None:
    """Store kcal_per_serving from the current ingredient list.

    Callers run this inside the same transaction that changed the ingredients,
    so the stored value can never disagree with the lines.
    """
    total = RecipeIngredient.objects.filter(recipe=recipe).aggregate(
        kcal=Sum(F("grams") * F("ingredient__kcal_per_100g") / 100)
    )["kcal"] or Decimal(0)
    recipe.kcal_per_serving = round(total / recipe.servings, 1)
    recipe.save(update_fields=["kcal_per_serving"])


@transaction.atomic
def replace_ingredients(recipe: Recipe, lines: list[dict]) -> None:
    """Delete the old lines, insert the new ones and recalculate, all or nothing."""
    RecipeIngredient.objects.filter(recipe=recipe).delete()
    RecipeIngredient.objects.bulk_create(
        RecipeIngredient(recipe=recipe, ingredient_id=line["ingredient_id"], grams=line["grams"])
        for line in lines
    )
    recalculate_kcal(recipe)


@transaction.atomic
def create_recipe(author_id: int, title: str, servings: int, lines: list[dict]) -> Recipe:
    recipe = Recipe.objects.create(author_id=author_id, title=title, servings=servings)
    replace_ingredients(recipe, lines)
    return recipe
