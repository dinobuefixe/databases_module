import json
import re

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from demo.clients import r
from demo.models import Film
from demo.patterns import allow_request, get_customer, leaderboard_key, record_rental, update_customer


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


@require_http_methods(["GET", "POST"])
def film_views(request: HttpRequest, film_id: int) -> JsonResponse:
    """String as a counter. INCR is atomic: concurrent requests never lose a view."""
    key = f"film:{film_id}:views"
    views = r.incr(key) if request.method == "POST" else int(r.get(key) or 0)
    return JsonResponse({"key": key, "views": views})


@require_http_methods(["GET", "POST"])
def film_hash(request: HttpRequest, film_id: int) -> JsonResponse:
    """Hash: a small object with named fields. POST copies two columns from PostgreSQL into it."""
    key = f"film:{film_id}"
    if request.method == "POST":
        film = Film.objects.filter(pk=film_id).values("title", "rental_rate").first()
        if film is None:
            return JsonResponse({"error": "Film not found"}, status=404)
        r.hset(key, mapping={"title": film["title"], "rate": str(film["rental_rate"])})
    fields = r.hgetall(key)
    if not fields:
        return JsonResponse({"error": f"{key} does not exist; POST to create it"}, status=404)
    return JsonResponse({"key": key, "fields": fields})


@require_http_methods(["GET", "POST"])
def visitors(request: HttpRequest, day: str) -> JsonResponse:
    """Set: adding the same customer twice on the same day counts once."""
    key = f"visitors:{day}"
    added = None
    if request.method == "POST":
        body = read_json(request)
        if body is None or not isinstance(body.get("customer_id"), int):
            return JsonResponse({"error": "customer_id (int) is required"}, status=422)
        added = r.sadd(key, f"customer:{body['customer_id']}")  # 1 if new, 0 if already there
    return JsonResponse({"key": key, "added": added, "unique_visitors": r.scard(key)})


@require_GET
def search(request: HttpRequest) -> JsonResponse:
    """Sorted set of search terms, and the fixed-window rate limit applied to this endpoint."""
    client = request.META.get("REMOTE_ADDR", "unknown")
    allowed, count, retry_after = allow_request(client, settings.RATE_LIMIT)
    if not allowed:
        response = JsonResponse(
            {"error": "Too many requests", "count": count, "limit": settings.RATE_LIMIT}, status=429
        )
        response["Retry-After"] = str(retry_after)
        return response

    term = request.GET.get("term", "").strip().lower()
    if not term:
        return JsonResponse({"error": "term is required"}, status=422)
    r.zincrby("search:terms", 1, term)
    titles = list(Film.objects.filter(title__icontains=term).order_by("title").values_list("title", flat=True)[:5])
    return JsonResponse({"term": term, "films": titles, "requests_this_minute": count})


@require_GET
def popular_terms(request: HttpRequest) -> JsonResponse:
    """ZRANGE search:terms 0 4 REV WITHSCORES: the five most searched terms."""
    top = r.zrange("search:terms", 0, 4, desc=True, withscores=True)
    return JsonResponse({"terms": [{"term": t, "searches": int(s)} for t, s in top]})


def week_key(request: HttpRequest) -> str | None:
    """?week=2026-W41 picks a past week; without it, this week. None if the format is wrong."""
    week = request.GET.get("week")
    if week is None:
        return leaderboard_key()
    return f"leaderboard:customers:{week}" if re.fullmatch(r"\d{4}-W\d{2}", week) else None


@require_GET
def leaderboard(request: HttpRequest) -> JsonResponse:
    """ZRANGE key 0 9 REV WITHSCORES (the same as ZREVRANGE key 0 9 WITHSCORES): the top 10."""
    key = week_key(request)
    if key is None:
        return JsonResponse({"error": "week must look like 2026-W41"}, status=422)
    top = r.zrange(key, 0, 9, desc=True, withscores=True)
    return JsonResponse(
        {
            "key": key,
            "ttl": r.ttl(key),
            "top": [{"rank": i, "member": m, "rentals": int(s)} for i, (m, s) in enumerate(top, start=1)],
        }
    )


@require_http_methods(["GET", "POST"])
def leaderboard_customer(request: HttpRequest, customer_id: int) -> JsonResponse:
    """POST records one rental this week. GET returns the rank: ZREVRANK counts from 0 for the top."""
    member = f"customer:{customer_id}"
    if request.method == "POST":
        key, _ = record_rental(customer_id)
    else:
        key = week_key(request)
        if key is None:
            return JsonResponse({"error": "week must look like 2026-W41"}, status=422)
    rank = r.zrevrank(key, member)
    if rank is None:
        return JsonResponse({"error": f"{member} is not in {key}"}, status=404)
    return JsonResponse({"key": key, "member": member, "rank": rank + 1, "rentals": int(r.zscore(key, member))})


@require_http_methods(["GET", "PATCH"])
def customer(request: HttpRequest, customer_id: int) -> JsonResponse:
    if request.method == "PATCH":
        body = read_json(request)
        allowed = {"first_name", "last_name", "email"}
        if not body or not set(body) <= allowed or not all(isinstance(v, str) for v in body.values()):
            return JsonResponse({"error": f"send one or more of {sorted(allowed)} as strings"}, status=422)
        if not update_customer(customer_id, body):
            return JsonResponse({"error": "Customer not found"}, status=404)

    data, cache = get_customer(customer_id)
    if data is None:
        return JsonResponse({"error": "Customer not found"}, status=404)
    return JsonResponse({"cache": cache, "customer": data})
