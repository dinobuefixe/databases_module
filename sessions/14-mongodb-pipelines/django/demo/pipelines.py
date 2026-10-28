"""The pipelines from the session 14 tutorial."""

from datetime import datetime, timedelta

from demo.clients import mongo_db


def films_per_rating() -> list[dict]:
    return list(
        mongo_db.films.aggregate(
            [
                {"$group": {"_id": "$rating", "films": {"$sum": 1}, "avg_rate": {"$avg": "$rental_rate"}}},
                {"$sort": {"films": -1}},
            ]
        )
    )


def top_actors(limit: int = 10) -> list[dict]:
    return list(
        mongo_db.films.aggregate(
            [
                # One document per (film, actor) pair, then count per actor.
                {"$unwind": "$actors"},
                {"$group": {"_id": "$actors.actor_id", "name": {"$first": "$actors.name"}, "films": {"$sum": 1}}},
                {"$sort": {"films": -1, "_id": 1}},
                {"$limit": limit},
            ]
        )
    )


# Also used by materialise_rentals_per_month, which writes the result with $merge.
RENTALS_PER_MONTH = [
    {"$unwind": "$recent_rentals"},
    {
        "$group": {
            "_id": {"$dateTrunc": {"date": "$recent_rentals.rental_date", "unit": "month"}},
            "rentals": {"$sum": 1},
        }
    },
]


def rentals_per_month() -> list[dict]:
    return list(mongo_db.customers.aggregate([*RENTALS_PER_MONTH, {"$sort": {"_id": 1}}]))


def customers_by_activity() -> list[dict]:
    """$bucket: customers grouped into ranges of total rentals. _id is the lower bound of each range."""
    return list(
        mongo_db.customers.aggregate(
            [
                {
                    "$bucket": {
                        "groupBy": "$rentals_total",
                        "boundaries": [0, 20, 40, 60, 80, 100],
                        "default": "other",  # where values outside the boundaries would go
                        "output": {"customers": {"$sum": 1}, "rentals": {"$sum": "$rentals_total"}},
                    }
                }
            ]
        )
    )


def customers_summary() -> dict:
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
    return next(mongo_db.customers.aggregate(pipeline))


def latest_rentals(limit: int = 5) -> list[dict]:
    """$lookup: the latest rentals with the rating and categories of the film, read from films."""
    return list(
        mongo_db.customers.aggregate(
            [
                {"$unwind": "$recent_rentals"},
                {"$sort": {"recent_rentals.rental_date": -1, "recent_rentals.rental_id": -1}},
                {"$limit": limit},
                # After $limit, so only `limit` documents look up their film, not every embedded rental.
                {
                    "$lookup": {
                        "from": "films",
                        "localField": "recent_rentals.film_id",
                        "foreignField": "_id",
                        "as": "film",
                    }
                },
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
        )
    )


def docs_examined(collection: str, pipeline: list) -> int:
    plan = mongo_db.command(
        {"explain": {"aggregate": collection, "pipeline": pipeline, "cursor": {}}, "verbosity": "executionStats"}
    )
    # When the whole pipeline runs in the query engine the stats are at the top;
    # otherwise they are in the first stage, $cursor.
    stats = plan.get("executionStats") or plan["stages"][0]["$cursor"]["executionStats"]
    return stats["totalDocsExamined"]


def match_position(start: datetime, days: int = 7) -> dict:
    """Rentals per store in a date range, with the $match late and early. Same result, different work."""
    in_range = {"$gte": start, "$lt": start + timedelta(days=days)}
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
        name: {"docs_examined": docs_examined("customers", p), "result": list(mongo_db.customers.aggregate(p))}
        for name, p in (("match_late", late), ("match_early", early))
    }


def materialise_rentals_per_month() -> dict:
    """$merge writes the pipeline result into a collection. _id is the month, so a second run
    replaces the same documents instead of adding new ones: running it again changes nothing."""
    mongo_db.customers.aggregate(
        [
            *RENTALS_PER_MONTH,
            {"$merge": {"into": "rentals_per_month", "on": "_id", "whenMatched": "replace", "whenNotMatched": "insert"}},
        ]
    )
    totals = {"_id": None, "months": {"$sum": 1}, "rentals": {"$sum": "$rentals"}}
    row = next(mongo_db.rentals_per_month.aggregate([{"$group": totals}]))
    return {"collection": "rentals_per_month", "months": row["months"], "rentals": row["rentals"]}
