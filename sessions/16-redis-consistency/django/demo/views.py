import json

import redis
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from demo.clients import r
from demo.derived import films_key, verify


@require_GET
def customer_films(request: HttpRequest, customer_id: int) -> JsonResponse:
    """Read from Redis only. If the set is missing, run the rebuild, not a query here."""
    films = sorted(int(f) for f in r.smembers(films_key(customer_id)))
    return JsonResponse({"customer_id": customer_id, "films": len(films), "film_ids": films})


@require_GET
def verify_view(request: HttpRequest) -> JsonResponse:
    """The verification as an endpoint: 200 when Redis matches PostgreSQL, 409 when it does not."""
    checked, errors = verify()
    return JsonResponse(
        {"ok": not errors, "checked": checked, "mismatches": len(errors), "first_mismatches": errors[:10]},
        status=200 if not errors else 409,
    )


@require_GET
def persistence(request: HttpRequest) -> JsonResponse:
    """Reads the server's persistence and memory settings. Read only: CONFIG SET is not used."""
    settings = {}
    for name in ("appendonly", "appendfsync", "save", "maxmemory", "maxmemory-policy"):
        settings.update(r.config_get(name))
    return JsonResponse(settings)


def change_username_watch(customer_id: int, new: str) -> bool:
    """Optimistic locking: if 'usernames' or the customer's hash changes between WATCH and EXEC, retry.

    The old name is read after WATCH, inside the retry loop. Read before it, two changes to
    the same customer could remove the same old name and leave the first new one in
    'usernames' with nobody using it.
    """
    customer_key = f"customer:{customer_id}"
    with r.pipeline() as pipe:
        while True:
            try:
                pipe.watch("usernames", customer_key)
                old = pipe.hget(customer_key, "username")
                if old == new:
                    pipe.unwatch()
                    return True
                if pipe.sismember("usernames", new):
                    pipe.unwatch()
                    return False
                pipe.multi()
                if old:
                    pipe.srem("usernames", old)
                pipe.sadd("usernames", new)
                pipe.hset(customer_key, "username", new)
                pipe.execute()
                return True
            except redis.WatchError:
                continue


# The same check and writes inside Redis, in one round trip and without retries.
# The script reads the old name itself, so nothing can change it in between.
change_username_script = r.register_script("""
if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 1 then
    return redis.call('HGET', KEYS[2], 'username') == ARGV[1] and 1 or 0
end
local old = redis.call('HGET', KEYS[2], 'username')
if old then redis.call('SREM', KEYS[1], old) end
redis.call('SADD', KEYS[1], ARGV[1])
redis.call('HSET', KEYS[2], 'username', ARGV[1])
return 1
""")


def change_username_lua(customer_id: int, new: str) -> bool:
    return change_username_script(keys=["usernames", f"customer:{customer_id}"], args=[new]) == 1


@require_http_methods(["PUT"])
def change_username(request: HttpRequest, customer_id: int) -> JsonResponse:
    impl = request.GET.get("impl", "watch")
    if impl not in ("watch", "lua"):
        return JsonResponse({"error": "impl must be watch or lua"}, status=422)
    try:
        new = json.loads(request.body).get("username")
    except (json.JSONDecodeError, AttributeError):
        new = None
    if not isinstance(new, str) or not new.strip():
        return JsonResponse({"error": "username must be a non-empty string"}, status=422)

    change = change_username_watch if impl == "watch" else change_username_lua
    if not change(customer_id, new):
        return JsonResponse({"error": f"username {new!r} is taken"}, status=409)
    return JsonResponse({"customer_id": customer_id, "username": new, "impl": impl})
