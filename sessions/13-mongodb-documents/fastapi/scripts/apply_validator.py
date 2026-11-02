"""Adds $jsonSchema validation to the stores collection.

Run with: uv run python -m scripts.apply_validator

collMod changes an existing collection. If the collection does not exist yet,
it is created with the validator instead.
"""

from app.clients import db

STORE_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["manager", "address"],
        "properties": {
            "manager": {"bsonType": "object", "required": ["staff_id", "name"]},
            "address": {
                "bsonType": "object",
                "required": ["city", "country"],
                "properties": {
                    "city": {"bsonType": "string"},
                    "country": {"bsonType": "string"},
                },
            },
            "staff": {"bsonType": "array"},
        },
    }
}


def main() -> None:
    options = {
        "validator": STORE_SCHEMA,
        # strict: every insert and update is checked, including updates to old documents.
        "validationLevel": "strict",
        # error: invalid writes are rejected (warn would only log them).
        "validationAction": "error",
    }
    if "stores" in db.list_collection_names():
        db.command({"collMod": "stores", **options})
        print("Validator applied to the existing stores collection")
    else:
        db.create_collection("stores", **options)
        print("Created stores with the validator")

    info = db.command("listCollections", filter={"name": "stores"})["cursor"]["firstBatch"][0]
    print("validationLevel:", info["options"]["validationLevel"])
    print("validationAction:", info["options"]["validationAction"])


if __name__ == "__main__":
    main()
