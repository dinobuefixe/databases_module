# Session 13 in FastAPI: MongoDB documents, CRUD and validation

Copies Pagila's stores from PostgreSQL into a `stores` collection with the address, manager and staff embedded, then queries and updates them with `pymongo`, adds `$jsonSchema` validation and compares `explain("executionStats")` before and after an index.

| File | What it shows |
|------|---------------|
| `app/clients.py` | `psycopg` connection for reading Pagila, `pymongo` client for our own Mongo database `s13_fastapi`. |
| `scripts/sync_stores.py` | Reads stores with address, city, country, manager and staff from PostgreSQL and upserts one document per store (`UpdateOne(..., upsert=True)` in a `bulk_write`). |
| `scripts/apply_validator.py` | The tutorial's `$jsonSchema` validator with `validationLevel: strict` and `validationAction: error`, applied with `collMod`. |
| `app/main.py` | `GET /stores?country=` (dot notation and projection), `GET /stores/{id}`, `POST /stores/{id}/staff` (`$push`), `POST /stores/{id}/visits` (`$inc`), `POST /stores` (raw insert, shows the validation error), `POST /stores/explain-index` (explain before and after the index). |

A store document looks like this:

```json
{
  "_id": 1,
  "manager": {"staff_id": 1, "name": "Warner Hudson"},
  "address": {"line": "569 Baicheng Lane", "city": "Boksburg", "country": "South Africa"},
  "staff": [{"staff_id": 6, "name": "Theo Harber"}, ...],
  "visits": 2
}
```

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s13_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.sync_stores        # 500 stores: 500 inserted
uv run python -m scripts.apply_validator
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8000/stores?country=Canada'
curl localhost:8000/stores/1
curl -X POST localhost:8000/stores/1/staff -H 'content-type: application/json' -d '{"staff_id": 9001, "name": "New Hire"}'
curl -X POST localhost:8000/stores/1/visits
curl -X POST localhost:8000/stores -H 'content-type: application/json' -d '{"_id": 9999, "address": {"city": 42}}'
curl -X POST 'localhost:8000/stores/explain-index?country=Canada'
```

The invalid insert returns 422 with MongoDB's `errInfo`: `city` has the wrong type, `country` and `manager` are missing. The explain call returns `COLLSCAN` with `totalDocsExamined` equal to the whole collection before the index, and `FETCH` over `IXSCAN` with `totalDocsExamined` equal to `nReturned` after it.

## Things to try

- Run `uv run python -m scripts.sync_stores` twice. The second run reports every store as unchanged: upserts on a fixed `_id` make the sync safe to repeat.
- Add a staff member with `$push`, then run the sync again: it reports 1 modified, because the staff list is replaced by the one from PostgreSQL. PostgreSQL is the source; the document is a copy.
- See what `validationLevel` changes. In `mongosh` (command below), remove the validator with `db.runCommand({ collMod: "stores", validator: {} })`, insert the invalid store `{"_id": 9999, "address": {"city": 42}}` with `POST /stores` (201 this time), run `uv run python -m scripts.apply_validator` again and call `POST /stores/9999/visits`. With `validationLevel: strict` the `$inc` is rejected with 422, because every update is checked. Change the script to `moderate`, run it again and repeat: the update goes through, because the document was already invalid before the validator existed.
- Open `mongosh` and run the tutorial commands against the same data (the password is the one in the repository's `.env`):

  ```bash
  docker compose exec mongo mongosh -u root -p change-me-mongo --authenticationDatabase admin s13_fastapi
  ```

  then `db.stores.find({ "address.country": "Canada" }, { _id: 1, "address.city": 1 })`.
- Try `country=India` in the explain endpoint. More documents match, so the gap between scanning everything and reading only the matches is smaller.
