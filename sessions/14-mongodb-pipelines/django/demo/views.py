from datetime import UTC, datetime

from bson import Decimal128
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from demo import pipelines
from demo.clients import mongo_db
from demo.reports import ReportExists, build_monthly_report, freeze_monthly_report, month_bounds


class MongoJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal128):
            return str(o.to_decimal())
        return super().default(o)


def ok(data, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status, encoder=MongoJSONEncoder, safe=False)


@require_GET
def films_per_rating(request: HttpRequest) -> JsonResponse:
    return ok(pipelines.films_per_rating())


@require_GET
def top_actors(request: HttpRequest) -> JsonResponse:
    try:
        limit = max(1, min(int(request.GET.get("limit", 10)), 50))
    except ValueError:
        limit = 10
    return ok(pipelines.top_actors(limit))


@require_GET
def rentals_per_month(request: HttpRequest) -> JsonResponse:
    return ok(pipelines.rentals_per_month())


@require_GET
def customers_by_activity(request: HttpRequest) -> JsonResponse:
    return ok(pipelines.customers_by_activity())


@require_GET
def customers_summary(request: HttpRequest) -> JsonResponse:
    return ok(pipelines.customers_summary())


@require_GET
def latest_rentals(request: HttpRequest) -> JsonResponse:
    try:
        limit = max(1, min(int(request.GET.get("limit", 5)), 50))
    except ValueError:
        limit = 5
    return ok(pipelines.latest_rentals(limit))


@require_GET
def match_position(request: HttpRequest) -> JsonResponse:
    try:
        start = datetime.strptime(request.GET.get("start", "2026-07-21"), "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return JsonResponse({"error": "start must be YYYY-MM-DD"}, status=422)
    return ok(pipelines.match_position(start))


@require_http_methods(["GET", "POST"])
def rentals_per_month_report(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        return ok(pipelines.materialise_rentals_per_month())
    # Reading a materialised report is a plain find: no pipeline runs.
    return ok(list(mongo_db.rentals_per_month.find().sort("_id", 1)))


@require_http_methods(["GET", "POST"])
def monthly_report(request: HttpRequest, month: str) -> JsonResponse:
    try:
        month_bounds(month)
    except ValueError:
        return JsonResponse({"error": f"{month} is not a valid month"}, status=422)

    if request.method == "GET":
        report = mongo_db.monthly_reports.find_one({"_id": month})
        if report is None:
            return JsonResponse({"error": f"Report {month} has not been generated"}, status=404)
        return ok(report)

    report = build_monthly_report(month)
    if not report["stores"]:
        return JsonResponse({"error": f"No payments in {month}"}, status=422)
    try:
        freeze_monthly_report(report)
    except ReportExists:
        return JsonResponse({"error": f"Report {month} already exists and is frozen"}, status=409)
    return ok(
        {
            "_id": month,
            "generated_at": report["generated_at"],
            "stores": len(report["stores"]),
            "payments": sum(s["payments"] for s in report["stores"]),
        },
        status=201,
    )
