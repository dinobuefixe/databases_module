import json
from decimal import Decimal, InvalidOperation

from django.db import connection, transaction
from django.http import HttpRequest, JsonResponse
from django.test.utils import CaptureQueriesContext
from django.views.decorators.http import require_GET, require_POST

from demo.models import Actor, Film

SORTS = {"title", "-title", "length", "-length", "rental_rate", "-rental_rate"}


def sql_of(ctx: CaptureQueriesContext) -> list[str]:
    return [q["sql"] for q in ctx.captured_queries]


def read_json(request: HttpRequest) -> dict:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return {}
    return body if isinstance(body, dict) else {}


@require_GET
def list_films(request: HttpRequest) -> JsonResponse:
    """GET /films?rating=R&q=love&sort=-length&limit=10&offset=0"""
    sort = request.GET.get("sort", "title")
    if sort not in SORTS:  # never pass user input straight into ORDER BY
        return JsonResponse({"error": f"sort must be one of {sorted(SORTS)}"}, status=400)
    try:
        limit = min(int(request.GET.get("limit", 10)), 100)
        offset = max(int(request.GET.get("offset", 0)), 0)
    except ValueError:
        return JsonResponse({"error": "limit and offset must be integers"}, status=400)

    qs = Film.objects.all()
    if rating := request.GET.get("rating"):
        qs = qs.filter(rating=rating)
    if q := request.GET.get("q"):
        # icontains: Django writes UPPER(title) LIKE UPPER('%love%'), not ILIKE.
        qs = qs.filter(title__icontains=q)

    with CaptureQueriesContext(connection) as ctx:
        rows = list(qs.order_by(sort, "film_id").values("film_id", "title", "length", "rating", "rental_rate")[offset : offset + limit])
    return JsonResponse({"films": rows, "sql": sql_of(ctx)})


@require_POST
def create_actor(request: HttpRequest) -> JsonResponse:
    """INSERT ... RETURNING: one round trip gives back the generated id and default."""
    body = read_json(request)
    first, last = body.get("first_name"), body.get("last_name")
    if not isinstance(first, str) or not isinstance(last, str) or not first or not last:
        return JsonResponse({"error": "first_name and last_name are required"}, status=400)
    with CaptureQueriesContext(connection) as ctx:
        actor = Actor.objects.create(first_name=first.upper(), last_name=last.upper())
    return JsonResponse(
        {"actor_id": actor.actor_id, "last_update": actor.last_update, "sql": sql_of(ctx)},
        status=201,
    )


class CountMismatch(Exception):
    pass


@require_POST
def update_rental_rate(request: HttpRequest) -> JsonResponse:
    """Safe UPDATE: change the rate only if the number of rows is the one expected.

    Body: {"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 73}
    Without "expected" it is a dry run that only reports how many rows match.
    """
    body = read_json(request)
    try:
        rating = str(body["rating"])
        below = Decimal(str(body["below"]))
        new_rate = Decimal(str(body["new_rate"])) if "new_rate" in body else None
    except (KeyError, InvalidOperation):
        return JsonResponse({"error": "rating and below are required, below and new_rate are numbers"}, status=400)

    qs = Film.objects.filter(rating=rating, rental_rate__lt=below)
    expected = body.get("expected")
    if expected is None or new_rate is None:
        return JsonResponse({"dry_run": True, "matching": qs.count()})

    try:
        with CaptureQueriesContext(connection) as ctx, transaction.atomic():
            # Lock the rows first so the list we return is exactly what we update.
            films = list(qs.select_for_update().order_by("film_id").values("film_id", "title"))
            updated = qs.update(rental_rate=new_rate)  # returns the row count, like UPDATE n
            if updated != expected:
                raise CountMismatch  # leaving the block with an exception means ROLLBACK
    except CountMismatch:
        return JsonResponse(
            {"error": "row count differs, rolled back", "expected": expected, "matched": updated, "sql": sql_of(ctx)},
            status=409,
        )
    return JsonResponse({"updated": updated, "rental_rate": new_rate, "films": films, "sql": sql_of(ctx)})


# Django's bulk_create(update_conflicts=True) can only write
# "SET views = EXCLUDED.views", i.e. replace the value; it cannot add 1 to the
# stored one. The upsert is therefore plain SQL, sent with a parameter.
UPSERT_VIEW = """
    INSERT INTO film_views (film_id, views) VALUES (%s, 1)
    ON CONFLICT (film_id) DO UPDATE SET views = film_views.views + 1
    RETURNING film_id, views
"""


@require_POST
def add_view(request: HttpRequest, film_id: int) -> JsonResponse:
    if not Film.objects.filter(pk=film_id).exists():
        return JsonResponse({"error": "film not found"}, status=404)
    with connection.cursor() as cur:
        cur.execute(UPSERT_VIEW, [film_id])
        fid, views = cur.fetchone()
    return JsonResponse({"film_id": fid, "views": views})
