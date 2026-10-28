# Session 13 in Django: documents, CRUD and validation in MongoDB

The session 13 tutorial with Django and `pymongo`: Pagila stores read through the Django ORM and written to MongoDB as documents with an embedded manager, address and staff list, then queried with dot notation, updated with `$push` and `$inc`, protected by a `$jsonSchema` validator and indexed, with `explain` before and after.

| File | What it shows |
|------|---------------|
| `demo/models.py` | The Pagila tables the sync reads (`store`, `staff`, `address`, `city`, `country`), unmanaged. |
| `demo/management/commands/sync_stores.py` | PostgreSQL to MongoDB: one document per store, upserted with `_id` = `store_id`, so running it twice changes nothing. |
| `demo/management/commands/apply_validator.py` | `create_collection` or `collMod` with the tutorial's `$jsonSchema`, `validationLevel: strict`, `validationAction: error`. |
| `demo/management/commands/explain_index.py` | `explain("executionStats")` for the country query, then `create_index`, then `explain` again. |
| `demo/documents.py` | The validator, a JSON encoder for `ObjectId`, and a helper that reduces `explain` output to stages, documents examined and keys examined. |
| `demo/views.py` | `GET /stores?country=`, `POST /stores`, `POST /stores/{id}/staff` (`$push`), `POST /stores/{id}/visits` (`$inc`), `GET /stores/explain?country=`. |

This Pagila copy has 500 stores and 1,500 staff (between 0 and 9 per store), so the scans in `explain` are large enough to compare.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s13_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate            # records the unmanaged models, creates no tables
uv run python manage.py apply_validator
uv run python manage.py sync_stores
uv run python manage.py explain_index      # COLLSCAN over 500 documents, then IXSCAN
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8001/stores?country=Canada'
curl -X POST localhost:8001/stores/1/staff -H 'content-type: application/json' -d '{"staff_id": 3000, "name": "New Hire"}'
curl -X POST localhost:8001/stores/1/visits
curl -X POST localhost:8001/stores -H 'content-type: application/json' -d '{"_id": 99, "address": {"city": 42}}'   # 422
curl -X POST localhost:8001/stores -H 'content-type: application/json' \
    -d '{"_id": 900, "manager": {"staff_id": 1, "name": "Ana Lopes"}, "address": {"line": "1 Main St", "city": "Faro", "country": "Portugal"}, "staff": []}'
curl 'localhost:8001/stores/explain?country=Canada'
```

The `422` response contains MongoDB's `errInfo`: which properties failed, the expected type and the missing fields.

## Things to try

- Open the data in `mongosh` (`docker compose exec mongo mongosh -u root -p change-me-mongo`, then `use s13_django`) and run the tutorial's `find` and `updateOne` commands by hand.
- `POST /stores/1/staff` and then run `sync_stores` again. The new staff member disappears, because the sync `$set`s the whole `staff` array from PostgreSQL. Which engine is the source of truth for staff here?
- Change `validationAction` to `warn` in `apply_validator.py`, run it, and insert the invalid document again. It is accepted and the server log records the failure.
- Insert a document with a different shape, for example without `staff`. The validator does not require it, so it is accepted: the collection holds documents of more than one shape.
- `find({"staff.name": "New Hire"})` uses a multikey index if you create one on `staff.name`. Create it and compare `explain` before and after.
