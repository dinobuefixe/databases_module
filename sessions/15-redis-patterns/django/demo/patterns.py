"""The patterns from the session 15 tutorial: cache-aside, a lock with safe release, a rate limit,
a weekly leaderboard.

Key names follow object:id:field and are listed in the README.
"""

import json
import time
import uuid
from datetime import date

from demo.clients import r
from demo.models import Customer

CUSTOMER_TTL = 300


def load_customer_from_postgres(customer_id: int) -> dict | None:
    return Customer.objects.filter(pk=customer_id).values("customer_id", "first_name", "last_name", "email").first()


def get_customer(customer_id: int) -> tuple[dict | None, str]:
    """Cache-aside: Redis first; on a miss, PostgreSQL, then store the result with a TTL."""
    key = f"cache:customer:{customer_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached), "hit"
    data = load_customer_from_postgres(customer_id)
    if data is not None:
        r.set(key, json.dumps(data), ex=CUSTOMER_TTL)
    return data, "miss"


def update_customer(customer_id: int, changes: dict) -> bool:
    """Write the source of truth first, then delete the cached copy."""
    updated = Customer.objects.filter(pk=customer_id).update(**changes)
    r.delete(f"cache:customer:{customer_id}")
    return updated == 1


# Delete the lock only if it still holds our token. GET and DEL run in one script,
# so no other client can take the lock between the check and the delete.
release = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
""")


def run_exclusively(name: str, job, ttl: int = 60) -> bool:
    token = str(uuid.uuid4())
    if not r.set(f"lock:{name}", token, nx=True, ex=ttl):
        return False
    try:
        job()
    finally:
        release(keys=[f"lock:{name}"], args=[token])
    return True


def allow_request(client_id: str, limit: int = 10) -> tuple[bool, int, int]:
    """Fixed window: one counter per client per minute. Returns (allowed, count, seconds left)."""
    now = time.time()
    window = int(now // 60)
    key = f"ratelimit:{client_id}:{window}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    count, _ = pipe.execute()
    return count <= limit, count, 60 - int(now % 60)


# Two weeks from the first write, so last week's board can still be read during this week.
LEADERBOARD_TTL = 14 * 24 * 3600


def leaderboard_key(day: date | None = None) -> str:
    """One sorted set per ISO week: leaderboard:customers:2026-W41."""
    year, week, _ = (day or date.today()).isocalendar()
    return f"leaderboard:customers:{year}-W{week:02d}"


def record_rental(customer_id: int) -> tuple[str, float]:
    """Adds one rental to the customer's score this week. Returns the key and the new score."""
    key = leaderboard_key()
    pipe = r.pipeline()  # MULTI/EXEC: the two commands run together, nothing in between
    pipe.zincrby(key, 1, f"customer:{customer_id}")
    # NX: only set the expiry if the key has none, which is on the first write of the week.
    pipe.expire(key, LEADERBOARD_TTL, nx=True)
    score, _ = pipe.execute()
    return key, score
