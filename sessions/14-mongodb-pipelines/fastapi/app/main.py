from datetime import UTC, date, datetime, time, timedelta

from bson.decimal128 import Decimal128
from fastapi import FastAPI, HTTPException, Path, Query
from pymongo.errors import DuplicateKeyError

from app.clients import db, pg_readonly

app = FastAPI(title="Session 14: MongoDB aggregation pipelines")

MONTH = Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2022-07"])


def plain(value):
    """Decimal128 is not JSON; send it as a string so no precision is lost."""
    if isinstance(value, Decimal128):
        return str(value.to_decimal())
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


@app.get("/pipelines/films-per-rating")
def films_per_rating():
    pipeline = [
        {"$group": {"_id": "$rating", "films": {"$sum": 1}, "avg_rate": {"$avg": "$rental_rate"}}},
        {"$sort": {"films": -1}},
    ]
    return plain(list(db.films.aggregate(pipeline)))


@app.get("/pipelines/top-actors")
def top_actors(limit: int = Query(10, ge=1, le=100)):
    pipeline = [
        # One document per (film, actor) pair, so actors can be grouped.
        {"$unwind": "$actors"},
        {"$group": {"_id": "$actors.actor_id", "name": {"$first": "$actors.name"}, "films": {"$sum": 1}}},
        {"$sort": {"films": -1, "_id": 1}},
        {"$limit": limit},
    ]
    return list(db.films.aggregate(pipeline))


# Also used by POST /reports/rentals-per-month, which materialises it with $merge.
RENTALS_PER_MONTH = [
    {"$unwind": "$recent_rentals"},
    {
        "$group": {
            "_id": {"$dateTrunc": {"date": "$recent_rentals.rental_date", "unit": "month"}},
            "rentals": {"$sum": 1},
        }
    },
]


@app.get("/pipelines/rentals-per-month")
def rentals_per_month():
    """Counts only the embedded recent rentals (the last 10 per customer), not the full history."""
    pipeline = [*RENTALS_PER_MONTH, {"$sort": {"_id": 1}}]
    return [{"month": row["_id"].strftime("%Y-%m"), "rentals": row["rentals"]} for row in db.customers.aggregate(pipeline)]


@app.get("/pipelines/customers-by-activity")
def customers_by_activity():
    """$bucket: customers grouped into ranges of total rentals. _id is the lower bound of each range."""
    pipeline = [
        {
            "$bucket": {
                "groupBy": "$rentals_total",
                "boundaries": [0, 20, 40, 60, 80, 100],
                "default": "other",  # where values outside the boundaries would go
                "output": {"customers": {"$sum": 1}, "rentals": {"$sum": "$rentals_total"}},
            }
        }
    ]
    return list(db.customers.aggregate(pipeline))


@app.get("/pipelines/customers-summary")
def customers_summary():
    """$facet: two sub-pipelines over the same customers, returned together in one document."""
    pipeline = [
        {
            "$facet": {
                "per_store": [
                    {"$group": {"_id": "$store_id", "customers": {"$sum": 1}, "rentals": {"$sum": "$rentals_total"}}},
                    {"$sort": {"_id": 1}},
                ],
                "most_active": [
                    {"$sort": {"rentals_total": -1, "_id": 1}},
                    {"$limit": 3},
                    {"$project": {"name": 1, "store_id": 1, "rentals_total": 1}},
                ],
            }
        }
    ]
    return next(db.customers.aggregate(pipeline))


@app.get("/pipelines/latest-rentals")
def latest_rentals(limit: int = Query(5, ge=1, le=50)):
    """$lookup: the latest rentals with the rating and categories of the film, read from films."""
    pipeline = [
        {"$unwind": "$recent_rentals"},
        {"$sort": {"recent_rentals.rental_date": -1, "recent_rentals.rental_id": -1}},
        {"$limit": limit},
        # After $limit, so only `limit` documents look up their film, not every embedded rental.
        {"$lookup": {"from": "films", "localField": "recent_rentals.film_id", "foreignField": "_id", "as": "film"}},
        {"$unwind": "$film"},
        {
            "$project": {
                "_id": 0,
                "customer": "$name",
                "rental_date": "$recent_rentals.rental_date",
                "title": "$film.title",
                "rating": "$film.rating",
                "categories": "$film.categories",
            }
        },
    ]
    return list(db.customers.aggregate(pipeline))


def docs_examined(collection: str, pipeline: list) -> int:
    plan = db.command(
        {"explain": {"aggregate": collection, "pipeline": pipeline, "cursor": {}}, "verbosity": "executionStats"}
    )
    # When the whole pipeline runs in the query engine the stats are at the top;
    # otherwise they are in the first stage, $cursor.
    stats = plan.get("executionStats") or plan["stages"][0]["$cursor"]["executionStats"]
    return stats["totalDocsExamined"]


@app.get("/pipelines/match-position")
def match_position(start: date = Query(date(2026, 7, 21)), days: int = Query(7, ge=1, le=31)):
    """Rentals per store in a date range, with the $match late and early. Same result, different work."""
    begin = datetime.combine(start, time(), UTC)
    in_range = {"$gte": begin, "$lt": begin + timedelta(days=days)}
    per_store = [{"$group": {"_id": "$store_id", "rentals": {"$sum": 1}}}, {"$sort": {"_id": 1}}]

    # Late: every customer is read and unwound, then the rentals outside the range are dropped.
    late = [{"$unwind": "$recent_rentals"}, {"$match": {"recent_rentals.rental_date": in_range}}, *per_store]
    # Early: first keep only customers with a rental in the range (this $match can use the
    # index on recent_rentals.rental_date), then unwind and filter the rentals as before.
    early = [
        {"$match": {"recent_rentals": {"$elemMatch": {"rental_date": in_range}}}},
        {"$unwind": "$recent_rentals"},
        {"$match": {"recent_rentals.rental_date": in_range}},
        *per_store,
    ]
    return {
        name: {"docs_examined": docs_examined("customers", p), "result": list(db.customers.aggregate(p))}
        for name, p in (("match_late", late), ("match_early", early))
    }


@app.post("/reports/rentals-per-month")
def materialise_rentals_per_month():
    """$merge writes the pipeline result into a collection. _id is the month, so a second run
    replaces the same documents instead of adding new ones: running it again changes nothing."""
    db.customers.aggregate(
        [
            *RENTALS_PER_MONTH,
            {"$merge": {"into": "rentals_per_month", "on": "_id", "whenMatched": "replace", "whenNotMatched": "insert"}},
        ]
    )
    totals = {"_id": None, "months": {"$sum": 1}, "rentals": {"$sum": "$rentals"}}
    row = next(db.rentals_per_month.aggregate([{"$group": totals}]))
    return {"collection": "rentals_per_month", "months": row["months"], "rentals": row["rentals"]}


@app.get("/reports/rentals-per-month")
def read_rentals_per_month():
    # Reading a materialised report is a plain find: no pipeline runs.
    rows = db.rentals_per_month.find().sort("_id", 1)
    return [{"month": row["_id"].strftime("%Y-%m"), "rentals": row["rentals"]} for row in rows]


REPORT_SQL = """
    SELECT st.store_id, count(*) AS payments, sum(p.amount) AS revenue
    FROM payment p
    JOIN staff st ON st.staff_id = p.staff_id
    WHERE p.payment_date >= %(start)s AND p.payment_date < %(start)s::date + interval '1 month'
    GROUP BY st.store_id
    ORDER BY st.store_id
"""


@app.post("/reports/monthly/{month}", status_code=201)
def create_monthly_report(month: str = MONTH):
    """Builds the report once from PostgreSQL. The _id is the month, so a second insert fails."""
    if db.monthly_reports.count_documents({"_id": month}, limit=1):
        raise HTTPException(409, f"Report {month} already exists and is frozen")

    start = date.fromisoformat(f"{month}-01")
    # A date range instead of to_char(payment_date, 'YYYY-MM') = %s: same rows, but
    # PostgreSQL can skip the payment partitions of other months.
    with pg_readonly() as pg:
        rows = pg.execute(REPORT_SQL, {"start": start}).fetchall()

    report = {
        "_id": month,
        "generated_at": datetime.now(UTC),
        "stores": [{"store_id": s, "payments": n, "revenue": str(r)} for s, n, r in rows],
    }
    try:
        db.monthly_reports.insert_one(report)
    except DuplicateKeyError:
        # Another request created it between our check and our insert: the unique _id decides.
        raise HTTPException(409, f"Report {month} already exists and is frozen")
    return {"_id": month, "stores": len(report["stores"]), "generated_at": report["generated_at"]}


@app.get("/reports/monthly/{month}")
def read_monthly_report(month: str = MONTH):
    report = db.monthly_reports.find_one({"_id": month})
    if report is None:
        raise HTTPException(404, f"No report for {month}")
    return report
