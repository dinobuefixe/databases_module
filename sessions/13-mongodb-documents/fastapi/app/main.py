from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, OperationFailure

from app.clients import db

app = FastAPI(title="Session 13: MongoDB documents")

COUNTRY_INDEX = "address.country_1"
DOCUMENT_VALIDATION_FAILURE = 121  # MongoDB error code when $jsonSchema rejects a write


def validation_error(exc: OperationFailure) -> HTTPException:
    """Turns a rejected write into a 422 that shows which rules the document broke."""
    return HTTPException(422, {"error": "Document failed validation", "details": exc.details.get("errInfo")})


class StaffMember(BaseModel):
    staff_id: int
    name: str = Field(min_length=1)


@app.get("/stores")
def stores_by_country(country: str = "Canada"):
    """Dot notation reaches inside the embedded address; the projection keeps two fields."""
    cursor = db.stores.find({"address.country": country}, {"_id": 1, "address.city": 1}).sort("_id", 1)
    return list(cursor)


@app.get("/stores/{store_id}")
def get_store(store_id: int):
    store = db.stores.find_one({"_id": store_id})
    if store is None:
        raise HTTPException(404, "Store not found")
    return store


@app.post("/stores/{store_id}/staff")
def add_staff(store_id: int, member: StaffMember):
    """$push appends to the embedded staff array, in place, without reading the document first."""
    store = db.stores.find_one_and_update(
        {"_id": store_id},
        {"$push": {"staff": member.model_dump()}},
        projection={"staff": 1},
        return_document=ReturnDocument.AFTER,
    )
    if store is None:
        raise HTTPException(404, "Store not found")
    return store


@app.post("/stores/{store_id}/visits")
def add_visit(store_id: int):
    """$inc is atomic and creates the field the first time."""
    try:
        store = db.stores.find_one_and_update(
            {"_id": store_id},
            {"$inc": {"visits": 1}},
            projection={"visits": 1},
            return_document=ReturnDocument.AFTER,
        )
    except OperationFailure as exc:
        # With validationLevel "strict", updating a document that was already
        # invalid is rejected too; with "moderate" it goes through.
        if exc.code == DOCUMENT_VALIDATION_FAILURE:
            raise validation_error(exc)
        raise
    if store is None:
        raise HTTPException(404, "Store not found")
    return store


@app.post("/stores", status_code=201)
def insert_store(document: dict = Body(...)):
    """Inserts the body as it is, so that MongoDB's validator, not Pydantic, decides.

    Run `uv run python -m scripts.apply_validator` first, then try an invalid document.
    """
    try:
        result = db.stores.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(409, "A store with this _id already exists")
    except OperationFailure as exc:
        if exc.code == DOCUMENT_VALIDATION_FAILURE:
            raise validation_error(exc)
        raise
    return {"inserted_id": str(result.inserted_id)}


def summarise(explain: dict) -> dict:
    """The parts of explain("executionStats") the tutorial asks you to read."""
    stages = []
    node = explain["queryPlanner"]["winningPlan"]
    node = node.get("queryPlan", node)  # newer servers wrap the plan in queryPlan
    while node:
        stages.append(node["stage"])
        node = node.get("inputStage")
    stats = explain["executionStats"]
    return {
        "stages": stages,  # COLLSCAN = full scan, IXSCAN = index
        "nReturned": stats["nReturned"],
        "totalDocsExamined": stats["totalDocsExamined"],
        "totalKeysExamined": stats["totalKeysExamined"],
        "executionTimeMillis": stats["executionTimeMillis"],
    }


def explain_find(country: str) -> dict:
    return db.command(
        "explain",
        {"find": "stores", "filter": {"address.country": country}},
        verbosity="executionStats",
    )


@app.post("/stores/explain-index")
def explain_index(country: str = "Canada"):
    """Runs the same find before and after creating the index on address.country."""
    try:
        db.stores.drop_index(COUNTRY_INDEX)  # start from no index, so "before" is a real before
    except OperationFailure:
        pass
    before = summarise(explain_find(country))
    db.stores.create_index({"address.country": 1})
    after = summarise(explain_find(country))
    return {"filter": {"address.country": country}, "before": before, "after": after}
