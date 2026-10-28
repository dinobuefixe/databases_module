import json
from datetime import UTC, datetime

from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from demo.clients import mongo_db, r
from demo.models import Hello


def check(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as exc:  # report any failure instead of crashing the health check
        return f"error: {exc}"


def ping_postgres() -> None:
    with connection.cursor() as cur:
        cur.execute("SELECT 1")


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """One cheap command per engine."""
    result = {
        "postgres": check(ping_postgres),
        "mongo": check(lambda: mongo_db.command("ping")),
        "redis": check(r.ping),
    }
    healthy = all(v == "ok" for v in result.values())
    return JsonResponse(result, status=200 if healthy else 503)


@require_http_methods(["GET", "POST"])
def hello(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        return write_hello(request)
    return read_hello()


def write_hello(request: HttpRequest) -> JsonResponse:
    """Write the same message to each engine."""
    try:
        msg = json.loads(request.body).get("msg")
    except (json.JSONDecodeError, AttributeError):
        msg = None
    if not isinstance(msg, str) or not msg.strip():
        return JsonResponse({"error": "msg must be a non-empty string"}, status=400)

    # PostgreSQL: a row in a table with a fixed structure, through the ORM.
    row = Hello.objects.create(msg=msg)

    # MongoDB: a document; the tags list needs no extra table.
    result = mongo_db.hello.insert_one({"msg": msg, "tags": ["a", "b"], "created_at": datetime.now(UTC)})

    # Redis: a key holding the last message and a counter.
    r.set("hello:last", msg)
    count = r.incr("hello:count")

    return JsonResponse(
        {
            "postgres": {"id": row.id, "msg": row.msg, "created_at": row.created_at},
            "mongo": {"_id": str(result.inserted_id)},
            "redis": {"last": msg, "count": count},
        },
        status=201,
    )


def read_hello() -> JsonResponse:
    """Read back what each engine holds."""
    rows = list(Hello.objects.order_by("-id").values("id", "msg", "created_at")[:5])
    docs = [{**doc, "_id": str(doc["_id"])} for doc in mongo_db.hello.find().sort("_id", -1).limit(5)]
    return JsonResponse(
        {
            "postgres": rows,
            "mongo": docs,
            "redis": {"last": r.get("hello:last"), "count": int(r.get("hello:count") or 0)},
        }
    )
