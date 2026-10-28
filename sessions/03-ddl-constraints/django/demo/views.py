import json

from django.db import IntegrityError, transaction
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from demo.errors import constraint_error
from demo.models import Author, Ingredient, Recipe, RecipeIngredient

# These views do almost no validation on purpose: the database rejects bad rows
# and the error names the constraint. A real API would also validate the body
# (types, required fields) and return 400 before it reaches the database.


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def bad_request() -> JsonResponse:
    return JsonResponse({"error": "invalid JSON body or missing field"}, status=400)


@require_POST
def create_author(request: HttpRequest) -> JsonResponse:
    body = read_json(request)
    if body is None or "name" not in body or "email" not in body:
        return bad_request()
    try:
        author = Author.objects.create(name=body["name"], email=body["email"])
    except IntegrityError as exc:
        return constraint_error(exc)
    return JsonResponse({"id": author.id, "name": author.name, "email": author.email, "created_at": author.created_at}, status=201)


@require_POST
def create_ingredient(request: HttpRequest) -> JsonResponse:
    body = read_json(request)
    if body is None or "name" not in body or "kcal_per_100g" not in body:
        return bad_request()
    try:
        ingredient = Ingredient.objects.create(name=body["name"], kcal_per_100g=body["kcal_per_100g"])
    except IntegrityError as exc:
        return constraint_error(exc)
    return JsonResponse({"id": ingredient.id, "name": ingredient.name, "kcal_per_100g": ingredient.kcal_per_100g}, status=201)


@require_POST
def create_recipe(request: HttpRequest) -> JsonResponse:
    body = read_json(request)
    if body is None or not {"author_id", "title", "servings"} <= body.keys():
        return bad_request()
    lines = body.get("ingredients", [])
    try:
        # The recipe and its lines are saved together or not at all. Django creates
        # foreign keys as DEFERRABLE INITIALLY DEFERRED, so a missing author or
        # ingredient is only reported when this block commits.
        with transaction.atomic():
            recipe = Recipe.objects.create(author_id=body["author_id"], title=body["title"], servings=body["servings"])
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(recipe=recipe, ingredient_id=line["ingredient_id"], grams=line["grams"])
                for line in lines
            )
    except IntegrityError as exc:
        return constraint_error(exc)
    except (KeyError, TypeError):
        return bad_request()
    return JsonResponse({"id": recipe.id, "title": recipe.title, "servings": recipe.servings, "ingredients": len(lines)}, status=201)
