from django.core.management.base import BaseCommand
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext

from demo.models import Author, Ingredient, Recipe, RecipeIngredient


class Command(BaseCommand):
    help = "Break each rule from the tutorial and print what the database says."

    def attempt(self, label: str, action) -> None:
        try:
            # One transaction per attempt: a failed statement does not affect the next.
            with transaction.atomic():
                action()
        except IntegrityError as exc:
            pg = exc.__cause__
            self.stdout.write(f"REJECTED  {label}\n          constraint {pg.diag.constraint_name}: {pg.diag.message_primary}")
        else:
            self.stdout.write(f"ACCEPTED  {label}")

    def handle(self, *args, **options):
        # Valid rows to break the rules against (created once, kept afterwards).
        ana, _ = Author.objects.get_or_create(email="ana@example.com", defaults={"name": "Ana"})
        flour, _ = Ingredient.objects.get_or_create(name="Flour", defaults={"kcal_per_100g": 364})
        milk, _ = Ingredient.objects.get_or_create(name="Milk", defaults={"kcal_per_100g": 42})
        pancakes, created = Recipe.objects.get_or_create(author=ana, title="Pancakes", defaults={"servings": 4})
        if created:
            RecipeIngredient.objects.create(recipe=pancakes, ingredient=flour, grams=200)

        self.stdout.write("Invalid inserts\n")
        self.attempt("ingredient with negative calories",
                     lambda: Ingredient.objects.create(name="Sugar", kcal_per_100g=-1))
        self.attempt("recipe by an author that does not exist",
                     lambda: Recipe.objects.create(author_id=999, title="Soup", servings=4))
        self.attempt("two authors with the same email",
                     lambda: Author.objects.bulk_create([Author(name="Ana 2", email="ana@example.com")]))
        self.attempt("ingredient name already in use",
                     lambda: Ingredient.objects.create(name="Flour", kcal_per_100g=340))
        self.attempt("same author, same title",
                     lambda: Recipe.objects.create(author=ana, title="Pancakes", servings=2))
        self.attempt("recipe for 0 servings",
                     lambda: Recipe.objects.create(author=ana, title="Air", servings=0))
        self.attempt("ingredient line with 0 grams",
                     lambda: RecipeIngredient.objects.create(recipe=pancakes, ingredient=milk, grams=0))

        self.stdout.write("\nON DELETE RESTRICT: delete an author who has recipes")
        self.attempt(f"delete author {ana.email}", lambda: Author.objects.filter(pk=ana.pk).delete())

        self.stdout.write("\nON DELETE CASCADE: delete a recipe and its lines go with it")
        soup = Recipe.objects.create(author=ana, title="Test soup", servings=2)
        RecipeIngredient.objects.create(recipe=soup, ingredient=flour, grams=30)
        before = RecipeIngredient.objects.filter(recipe_id=soup.pk).count()
        # DB_CASCADE: Django sends a single DELETE FROM recipe and PostgreSQL removes the lines.
        with CaptureQueriesContext(connection) as ctx:
            Recipe.objects.filter(pk=soup.pk).delete()
        for query in ctx.captured_queries:
            self.stdout.write(f"          SQL sent by Django: {query['sql']}")
        after = RecipeIngredient.objects.filter(recipe_id=soup.pk).count()
        self.stdout.write(f"ACCEPTED  delete recipe {soup.pk}: lines before {before}, after {after}")
