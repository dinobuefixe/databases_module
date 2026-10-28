"""The stores collection: its validator and a short summary of explain() output."""

from bson import ObjectId
from django.core.serializers.json import DjangoJSONEncoder

from demo.clients import mongo_db


class MongoJSONEncoder(DjangoJSONEncoder):
    """JsonResponse encoder that also accepts the ObjectId the driver generates for _id."""

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

STORE_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["manager", "address"],
        "properties": {
            "manager": {"bsonType": "object", "required": ["staff_id", "name"]},
            "address": {
                "bsonType": "object",
                "required": ["city", "country"],
                "properties": {"city": {"bsonType": "string"}, "country": {"bsonType": "string"}},
            },
            "staff": {"bsonType": "array"},
        },
    }
}

COUNTRY_INDEX = "address.country_1"


def explain_find(country: str) -> dict:
    """Runs explain("executionStats") on find({"address.country": country})."""
    result = mongo_db.command(
        "explain",
        {"find": "stores", "filter": {"address.country": country}},
        verbosity="executionStats",
    )
    plan = result["queryPlanner"]["winningPlan"]
    plan = plan.get("queryPlan", plan)  # the slot-based engine nests the plan one level deeper
    stages = []
    while plan:
        stages.append(plan["stage"])
        plan = plan.get("inputStage")
    stats = result["executionStats"]
    return {
        "stages": stages,  # COLLSCAN (full scan) or FETCH <- IXSCAN (index)
        "nReturned": stats["nReturned"],
        "totalDocsExamined": stats["totalDocsExamined"],
        "totalKeysExamined": stats["totalKeysExamined"],
        "executionTimeMillis": stats["executionTimeMillis"],
    }
