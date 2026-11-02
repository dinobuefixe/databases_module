import json

from demo.clients import r
from demo.models import Customer, FilmReview

PROFILE_TTL = 300


def profile_key(customer_id: int) -> str:
    return f"profile:{customer_id}"


def load_profile(customer_id: int) -> dict | None:
    customer = Customer.objects.filter(pk=customer_id).values("customer_id", "first_name", "last_name", "email").first()
    if customer is None:
        return None
    customer["reviews"] = list(
        FilmReview.objects.filter(customer_id=customer_id).order_by("-created_at").values("film_id", "stars")[:5]
    )
    return customer


def get_profile(customer_id: int) -> dict | None:
    cached = r.get(profile_key(customer_id))
    if cached is not None:
        return json.loads(cached)
    profile = load_profile(customer_id)
    if profile is not None:
        r.set(profile_key(customer_id), json.dumps(profile), ex=PROFILE_TTL)
    return profile
