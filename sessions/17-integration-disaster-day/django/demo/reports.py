"""The frozen monthly report from session 14: built once from PostgreSQL, never rewritten."""

from datetime import UTC, datetime

from django.db.models import Count, Sum
from pymongo.errors import DuplicateKeyError

from demo.clients import mongo_db
from demo.models import Payment


class ReportExists(Exception):
    pass


def month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
    end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    return start, end


def build_monthly_report(month: str) -> dict:
    start, end = month_bounds(month)
    rows = (
        Payment.objects.using("readonly")
        .filter(payment_date__gte=start, payment_date__lt=end)
        .values("staff__store_id")
        .annotate(payments=Count("*"), revenue=Sum("amount"))
        .order_by("staff__store_id")
    )
    return {
        "_id": month,
        "generated_at": datetime.now(UTC),
        "stores": [
            {"store_id": r["staff__store_id"], "payments": r["payments"], "revenue": str(r["revenue"])} for r in rows
        ],
    }


def freeze_monthly_report(report: dict) -> None:
    try:
        mongo_db.monthly_reports.insert_one(report)
    except DuplicateKeyError:
        raise ReportExists(report["_id"]) from None
