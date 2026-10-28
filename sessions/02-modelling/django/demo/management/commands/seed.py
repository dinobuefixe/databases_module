from django.core.management.base import BaseCommand

from demo.models import Author, Ingredient, Recipe
from demo.services import create_recipe

# The three spreadsheet rows from the tutorial:
#   1 | Pancakes | Ana | ana@example.com | Flour | 364 | 200
#   1 | Pancakes | Ana | ana@example.com | Milk  |  42 | 300
#   2 | Omelette | Rui | rui@example.com | Egg   | 155 | 120
# The spreadsheet has no servings column; the model needs one, so we pick 4 and 1.


class Command(BaseCommand):
    help = "Load the tutorial spreadsheet, normalised into four tables."

    def handle(self, *args, **options):
        if Recipe.objects.exists():
            self.stdout.write("Already seeded.")
            return

        # Each author and each ingredient is stored once.
        ana = Author.objects.create(name="Ana", email="ana@example.com")
        rui = Author.objects.create(name="Rui", email="rui@example.com")
        flour = Ingredient.objects.create(name="Flour", kcal_per_100g=364)
        milk = Ingredient.objects.create(name="Milk", kcal_per_100g=42)
        egg = Ingredient.objects.create(name="Egg", kcal_per_100g=155)

        create_recipe(ana.id, "Pancakes", 4, [
            {"ingredient_id": flour.id, "grams": 200},
            {"ingredient_id": milk.id, "grams": 300},
        ])
        create_recipe(rui.id, "Omelette", 1, [{"ingredient_id": egg.id, "grams": 120}])

        for recipe in Recipe.objects.order_by("id"):
            self.stdout.write(f"{recipe.id} {recipe.title}: {recipe.kcal_per_serving} kcal per serving")
