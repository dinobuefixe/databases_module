import json
from functools import wraps

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import DatabaseError, connection, connections
from django.db.models import Count
from django.http import Http404, HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from demo.clients import mongo_db, r
from demo.models import Customer

FIELDS = ("customer_id", "first_name", "last_name", "email")


def local_demo_only(view):
    """The unsafe views answer 404 unless DEBUG is on."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404
        return view(request, *args, **kwargs)

    return wrapper


@require_GET
def whoami(request: HttpRequest) -> JsonResponse:
    """Which account the application uses on each engine."""

    def pg_user(alias: str) -> str:
        with connections[alias].cursor() as cur:
            cur.execute("SELECT current_user")
            return cur.fetchone()[0]

    return JsonResponse(
        {
            "postgres": pg_user("default"),
            "postgres_reports": pg_user("readonly"),
            "mongo": mongo_db.command("connectionStatus")["authInfo"]["authenticatedUsers"],
            "redis": r.acl_whoami(),
        }
    )


# --- SQL injection ---------------------------------------------------------------


@require_GET
@local_demo_only
def search_customers_unsafe(request: HttpRequest) -> JsonResponse:
    """UNSAFE, local demo only. The input is pasted into the SQL text and becomes code."""
    email = request.GET.get("email", "")
    query = f"SELECT customer_id, first_name, last_name, email FROM customer WHERE email = '{email}'"
    try:
        with connection.cursor() as cur:
            cur.execute(query)
            rows = [dict(zip(FIELDS, row)) for row in cur.fetchall()]
    except DatabaseError as exc:
        # Show what PostgreSQL said about the injected SQL.
        return JsonResponse({"sql": query, "error": str(exc).splitlines()[0]}, status=500)
    return JsonResponse({"sql": query, "row_count": len(rows), "rows": rows[:5]})


@require_GET
def search_customers(request: HttpRequest) -> JsonResponse:
    """Safe. The ORM sends the value as a parameter; it is never parsed as SQL.

    The same with a cursor: cur.execute("... WHERE email = %s", [email]).
    """
    email = request.GET.get("email", "")
    qs = Customer.objects.filter(email=email).values(*FIELDS)
    rows = list(qs)
    sql, params = qs.query.sql_with_params()
    return JsonResponse({"sql": sql, "params": params, "row_count": len(rows), "rows": rows[:5]})


@require_GET
def customers_per_store(request: HttpRequest) -> JsonResponse:
    """A report through the readonly role: .using("readonly") picks the other connection."""
    rows = Customer.objects.using("readonly").values("store_id").annotate(customers=Count("*")).order_by("store_id")
    return JsonResponse({"rows": list(rows)})


# --- NoSQL injection -------------------------------------------------------------


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


@require_POST
@local_demo_only
def login_unsafe(request: HttpRequest) -> JsonResponse:
    """UNSAFE, local demo only. The filter is built from the raw JSON body.

    {"username": "admin", "password": {"$ne": null}} turns the password check into
    "password is not null", which matches. It reads legacy_users, which stores
    plain-text passwords as old code often did: a second mistake.
    """
    body = read_json(request) or {}
    user = mongo_db.legacy_users.find_one({"username": body.get("username"), "password": body.get("password")})
    if user is None:
        return JsonResponse({"error": "invalid credentials"}, status=401)
    return JsonResponse({"logged_in_as": user["username"]})


@require_POST
def login(request: HttpRequest) -> JsonResponse:
    """Safe. Strings only, a lookup by username only, then an argon2 hash check."""
    body = read_json(request)
    username = body.get("username") if body else None
    password = body.get("password") if body else None
    if not isinstance(username, str) or not isinstance(password, str):
        # {"$ne": null} is a dict, not a string, so it never reaches MongoDB.
        return JsonResponse({"error": "username and password must be strings"}, status=400)

    user = mongo_db.users.find_one({"username": username})
    # check_password with an empty hash still runs the hasher, so an unknown user
    # takes about as long as a wrong password. Same answer for both.
    if not check_password(password, user["password_hash"] if user else ""):
        return JsonResponse({"error": "invalid credentials"}, status=401)
    return JsonResponse({"logged_in_as": user["username"]})
