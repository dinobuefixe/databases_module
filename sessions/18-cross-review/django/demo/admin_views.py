import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from demo.clients import r
from demo.models import Customer
from demo.profiles import load_profile, profile_key


@require_http_methods(["PUT"])
def update_profile(request: HttpRequest, customer_id: int) -> JsonResponse:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "body must be JSON"}, status=400)
    allowed = {"first_name", "last_name", "email"}
    if not isinstance(body, dict) or not body or not set(body) <= allowed:
        return JsonResponse({"error": f"send one or more of {sorted(allowed)}"}, status=422)

    if Customer.objects.filter(pk=customer_id).update(**body) == 0:
        return JsonResponse({"error": "Customer not found"}, status=404)
    profile = load_profile(customer_id)
    r.set(profile_key(customer_id), json.dumps(profile))
    return JsonResponse(profile)
