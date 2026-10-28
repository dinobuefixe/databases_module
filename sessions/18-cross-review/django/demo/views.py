import json

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from demo.clients import mongo_db, r
from demo.models import Customer, Film, FilmReview
from demo.profiles import get_profile


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


@require_GET
def search_films(request: HttpRequest) -> JsonResponse:
    title = request.GET.get("title", "")
    with connection.cursor() as cur:
        cur.execute(f"SELECT film_id, title FROM film WHERE title ILIKE '%{title}%' ORDER BY title LIMIT 20")
        rows = cur.fetchall()
    return JsonResponse({"films": [{"film_id": f, "title": t} for f, t in rows]})


@require_GET
def customer_by_email(request: HttpRequest) -> JsonResponse:
    email = request.GET.get("email", "")
    customer = Customer.objects.filter(email__iexact=email).values("customer_id", "first_name", "last_name").first()
    if customer is None:
        return JsonResponse({"error": "Customer not found"}, status=404)
    return JsonResponse(customer)


@require_GET
def profile(request: HttpRequest, customer_id: int) -> JsonResponse:
    data = get_profile(customer_id)
    if data is None:
        return JsonResponse({"error": "Customer not found"}, status=404)
    return JsonResponse(data)


@require_http_methods(["GET", "POST"])
def film_reviews(request: HttpRequest, film_id: int) -> JsonResponse:
    if not Film.objects.filter(pk=film_id).exists():
        return JsonResponse({"error": "Film not found"}, status=404)

    if request.method == "GET":
        reviews = list(
            FilmReview.objects.filter(film_id=film_id)
            .order_by("-created_at")
            .values("id", "customer_id", "stars", "comment", "created_at")[:20]
        )
        return JsonResponse({"film_id": film_id, "reviews": int(r.get(f"film:{film_id}:reviews") or 0), "latest": reviews})

    body = read_json(request) or {}
    if not isinstance(body.get("customer_id"), int) or not isinstance(body.get("stars"), int):
        return JsonResponse({"error": "customer_id and stars are required integers"}, status=422)
    review = FilmReview.objects.create(
        film_id=film_id, customer_id=body["customer_id"], stars=body["stars"], comment=str(body.get("comment", ""))
    )
    r.incr(f"film:{film_id}:reviews")
    mongo_db.activity.insert_one(
        {"type": "review", "customer_id": body["customer_id"], "film_id": film_id, "at": timezone.now()}
    )
    return JsonResponse({"id": review.id, "film_id": film_id, "stars": review.stars}, status=201)


@require_POST
def search_activity(request: HttpRequest) -> JsonResponse:
    body = read_json(request)
    if body is None:
        return JsonResponse({"error": "body must be a JSON object"}, status=400)
    events = list(mongo_db.activity.find(body, {"_id": 0}).sort("at", -1).limit(50))
    return JsonResponse({"events": events})
