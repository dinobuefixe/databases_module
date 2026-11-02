"""The frozen monthly report: built once from PostgreSQL, never rewritten."""

from datetime import UTC, datetime

from django.db.models import Count, Sum
from pymongo.errors import DuplicateKeyError

from demo.clients import mongo_db
from demo.models import Payment


class ReportExists(Exception):
    pass


def month_bounds(month: str) -> tuple[datetime, datetime]:
    """'2022-07' -> (2022-07-01, 2022-08-01). Raises ValueError for a month such as 2022-13."""
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
    end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
    return start, end


def build_monthly_report(month: str) -> dict:
    start, end = month_bounds(month)
    # A range on payment_date lets PostgreSQL read only that month's partition;
    # the tutorial's to_char(payment_date, 'YYYY-MM') = %s would scan all of them.
    rows = (
        Payment.objects.using("readonly")
        .filter(payment_date__gte=start, payment_date__lt=end)
        .values("staff__store_id")
        .annotate(payments=Count("*"), revenue=Sum("amount"))
        .order_by("staff__store_id")
    )
    return {
        "_id": month,  # deterministic: the same month always has the same _id
        "generated_at": datetime.now(UTC),
        "stores": [
            {"store_id": r["staff__store_id"], "payments": r["payments"], "revenue": str(r["revenue"])}
            for r in rows
        ],
    }


def freeze_monthly_report(report: dict) -> None:
    try:
        mongo_db.monthly_reports.insert_one(report)
    except DuplicateKeyError:
        # insert_one, not an upsert: a second run must not replace what was sent.
        raise ReportExists(report["_id"]) from None
