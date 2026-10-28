import json
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, connection
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.test.utils import CaptureQueriesContext
from django.views.decorators.http import require_GET, require_http_methods

from demo.models import Recipe
from demo.services import create_recipe, replace_ingredients


def parse_lines(raw) -> list[dict]:
    """Validate [{"ingredient_id": 1, "grams": 200}, ...]."""
    if not isinstance(raw, list) or not raw:
        raise ValueError("ingredients must be a non-empty list")
    lines = []
    for item in raw:
        try:
            lines.append({"ingredient_id": int(item["ingredient_id"]), "grams": Decimal(str(item["grams"]))})
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise ValueError("each ingredient needs ingredient_id and grams") from None
    return lines


def recipe_json(recipe: Recipe) -> dict:
    lines = recipe.recipeingredient_set.select_related("ingredient").order_by("ingredient__name")
    return {
        "id": recipe.id,
        "title": recipe.title,
        "author": {"id": recipe.author.id, "name": recipe.author.name, "email": recipe.author.email},
        "servings": recipe.servings,
        "kcal_per_serving": recipe.kcal_per_serving,
        "ingredients": [
            {
                "ingredient_id": line.ingredient.id,
                "name": line.ingredient.name,
                "kcal_per_100g": line.ingredient.kcal_per_100g,
                "grams": line.grams,
            }
            for line in lines
        ],
    }


@require_http_methods(["GET", "POST"])
def recipes(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        return post_recipe(request)

    # The listing reads the stored kcal_per_serving: one query on one table, no join.
    with CaptureQueriesContext(connection) as ctx:
        rows = list(Recipe.objects.order_by("id").values("id", "title", "servings", "kcal_per_serving"))
    return JsonResponse({"recipes": rows, "sql": [q["sql"] for q in ctx.captured_queries]})


def post_recipe(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body)
        lines = parse_lines(body.get("ingredients"))
        recipe = create_recipe(int(body["author_id"]), str(body["title"]), int(body["servings"]), lines)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return JsonResponse({"error": str(exc) or "invalid body"}, status=400)
    except IntegrityError as exc:
        # An unknown author or ingredient id breaks a foreign key.
        return JsonResponse({"error": str(exc).splitlines()[0]}, status=422)
    return JsonResponse(recipe_json(recipe), status=201)


@require_GET
def recipe_detail(request: HttpRequest, recipe_id: int) -> JsonResponse:
    recipe = get_object_or_404(Recipe.objects.select_related("author"), pk=recipe_id)
    return JsonResponse(recipe_json(recipe))


@require_http_methods(["PUT"])
def recipe_ingredients(request: HttpRequest, recipe_id: int) -> JsonResponse:
    """Replace the whole ingredient list; kcal_per_serving changes in the same transaction."""
    recipe = get_object_or_404(Recipe.objects.select_related("author"), pk=recipe_id)
    try:
        lines = parse_lines(json.loads(request.body).get("ingredients"))
        replace_ingredients(recipe, lines)
    except (json.JSONDecodeError, AttributeError, ValueError) as exc:
        return JsonResponse({"error": str(exc) or "invalid body"}, status=400)
    except IntegrityError as exc:
        return JsonResponse({"error": str(exc).splitlines()[0]}, status=422)
    return JsonResponse(recipe_json(recipe))
