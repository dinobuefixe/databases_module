import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, WriteError

from demo.clients import stores
from demo.documents import MongoJSONEncoder, explain_find


def read_json(request: HttpRequest) -> dict | None:
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


@require_http_methods(["GET", "POST"])
def stores_collection(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        return insert_store(request)
    return find_by_country(request)


def find_by_country(request: HttpRequest) -> JsonResponse:
    """find({"address.country": ...}, {"_id": 1, "address.city": 1}): dot notation and a projection."""
    country = request.GET.get("country", "")
    docs = list(stores.find({"address.country": country}, {"_id": 1, "address.city": 1}).sort("_id", 1))
    return JsonResponse({"country": country, "count": len(docs), "stores": docs}, encoder=MongoJSONEncoder)


def insert_store(request: HttpRequest) -> JsonResponse:
    """Inserts the body as it is, so you can see the validator accept or reject it."""
    doc = read_json(request)
    if doc is None:
        return JsonResponse({"error": "body must be a JSON object"}, status=400)
    try:
        result = stores.insert_one(doc)
    except DuplicateKeyError:
        return JsonResponse({"error": f"a store with _id {doc.get('_id')} already exists"}, status=409)
    except WriteError as exc:
        # Code 121 is "Document failed validation"; details says which rule failed.
        return JsonResponse(
            {"error": exc.details.get("errmsg"), "details": exc.details.get("errInfo")}, status=422
        )
    # Without an _id in the body, the driver generates an ObjectId.
    return JsonResponse({"_id": result.inserted_id}, status=201, encoder=MongoJSONEncoder)


@require_POST
def add_staff(request: HttpRequest, store_id: int) -> JsonResponse:
    """$push appends one element to the embedded staff array."""
    body = read_json(request)
    if body is None or not isinstance(body.get("staff_id"), int) or not isinstance(body.get("name"), str):
        return JsonResponse({"error": "staff_id (int) and name (string) are required"}, status=422)
    doc = stores.find_one_and_update(
        {"_id": store_id},
        {"$push": {"staff": {"staff_id": body["staff_id"], "name": body["name"]}}},
        projection={"staff": 1},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return JsonResponse({"error": "Store not found"}, status=404)
    return JsonResponse(doc, encoder=MongoJSONEncoder)


@require_POST
def add_visit(request: HttpRequest, store_id: int) -> JsonResponse:
    """$inc adds 1 to visits, and creates the field the first time."""
    doc = stores.find_one_and_update(
        {"_id": store_id},
        {"$inc": {"visits": 1}},
        projection={"visits": 1},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return JsonResponse({"error": "Store not found"}, status=404)
    return JsonResponse(doc, encoder=MongoJSONEncoder)


@require_GET
def explain(request: HttpRequest) -> JsonResponse:
    """The current plan for the country query. Run explain_index to compare without and with the index."""
    country = request.GET.get("country", "India")
    return JsonResponse({"country": country, **explain_find(country)})
