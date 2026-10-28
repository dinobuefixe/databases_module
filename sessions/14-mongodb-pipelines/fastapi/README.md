# Session 14 in FastAPI: MongoDB aggregation pipelines and frozen reports

Loads `films` and `customers` collections from Pagila, runs the tutorial's aggregation pipelines (`$group`, `$unwind`, `$dateTrunc`, `$bucket`, `$facet`, `$lookup`, `$match` early and late, `$merge`), writes a frozen monthly report that cannot be written twice, and backs up and restores this project's Mongo database.

| File | What it shows |
|------|---------------|
| `scripts/load_collections.py` | Builds `films` (`length`, the list of `categories` and the actors embedded, `rental_rate` as `Decimal128`) and `customers` (`store_id`, last 10 rentals embedded, total count, rest left in PostgreSQL), plus an index on `recent_rentals.rental_date`. |
| `app/main.py` | One endpoint per pipeline (below), `POST /reports/rentals-per-month` (`$merge` into a collection), `POST /reports/monthly/{YYYY-MM}` (201, then 409) and `GET /reports/monthly/{YYYY-MM}`. |
| `app/clients.py` | `pg_readonly()` opens a connection whose transactions are `READ ONLY`, for the report. |
| `scripts/backup_mongo.sh` | `mongodump --db s14_fastapi --archive --gzip` into `backups/` (git-ignored). Writes to a `.part` file and renames it only when the dump succeeds. |
| `scripts/restore_mongo.sh` | `mongorestore --nsFrom 's14_fastapi.*' --nsTo 's14_fastapi_restored.*'` with timing. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s14_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.load_collections     # films: 1000, customers: 999
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl localhost:8000/pipelines/films-per-rating
curl 'localhost:8000/pipelines/top-actors?limit=10'
curl localhost:8000/pipelines/rentals-per-month
curl localhost:8000/pipelines/customers-by-activity   # $bucket on rentals_total
curl localhost:8000/pipelines/customers-summary       # $facet: per store and the 3 most active
curl localhost:8000/pipelines/latest-rentals          # $lookup the film of the 5 latest rentals
curl localhost:8000/pipelines/match-position          # docs_examined: 999 with $match late, 164 early
curl -X POST localhost:8000/reports/rentals-per-month # {"months": 26, "rentals": 9622}, the same every time
curl localhost:8000/reports/rentals-per-month
curl -i -X POST localhost:8000/reports/monthly/2022-07     # 201 Created
curl -i -X POST localhost:8000/reports/monthly/2022-07     # 409 Conflict: frozen
curl localhost:8000/reports/monthly/2022-07
```

Backup and restore (the scripts call `docker compose exec` from the repository root for you). `mongodump` and `mongorestore` run inside the `mongo` container, where the server is `localhost:27017` whatever port your machine publishes, so the scripts build that URL with the root user from the `.env` at the root of the repository instead of using `MONGO_URL`:

```bash
./scripts/backup_mongo.sh
./scripts/restore_mongo.sh                 # newest file in backups/, into s14_fastapi_restored
```

## Notes

- **Frozen report.** The `_id` is the month, so MongoDB's unique `_id` index is what stops a second report. The endpoint checks first to avoid a useless query on PostgreSQL, but the `DuplicateKeyError` handler is what holds when two requests arrive together: fire ten at once and exactly one gets 201.
- **Date filter.** The tutorial filters with `to_char(payment_date, 'YYYY-MM') = '2022-07'`. This project uses `payment_date >= '2022-07-01' AND payment_date < '2022-08-01'`, which returns the same rows and lets PostgreSQL skip the `payment` partitions of other months.
- **Restore without `--drop` on the real database.** The tutorial restores with `--drop` into the original database, which replaces its collections. Here `--nsFrom/--nsTo` sends everything to `s14_fastapi_restored`, so `--drop` only replaces collections in that copy. In your own environment, restoring over the original database is the real disaster recovery step; restoring into a copy first is how you test a backup without risk.
- `rentals-per-month` counts only the 10 embedded rentals per customer, so recent months dominate. The full history lives in PostgreSQL.
- **`$lookup` sparingly.** `latest-rentals` reads the film's rating and categories from `films` with `$lookup`, after `$limit`, so it looks up 5 films. If most queries need the rating next to a rental, copy it into `recent_rentals` in the loader instead: a join on every read is a sign the data is relational or should be embedded.
- **`$match` first.** In `match-position` both pipelines return the same numbers. The late `$match` filters array elements after `$unwind`, so MongoDB cannot move it earlier and reads all 999 customers. The early one keeps only customers with a rental in the range, uses the index on `recent_rentals.rental_date`, and reads 164.
- **`$merge` is idempotent here.** The `_id` of each document is the month, and `whenMatched: "replace"` overwrites the document for a month that already exists. Run it twice and `rentals_per_month` has the same 26 documents. `$out` would also work, but it replaces the whole collection on every run.

## Things to try

- In `films-per-rating`, add `{"$match": {"rating": "PG"}}` as the first stage, then move it to the end as `{"$match": {"_id": "PG"}}` (after `$group` the rating is in `_id`). Compare `db.films.explain("executionStats").aggregate([...])` for both in `mongosh`: MongoDB moves a `$match` on the group key before `$group` for you, so both read the same documents. It cannot do that in `match-position`, because there the filter is on the elements that `$unwind` produces.
- Change a few rentals' dates in `s14_fastapi.customers` and call `POST /reports/rentals-per-month` again: only the months you touched change in `rentals_per_month`. Then replace `$merge` with `{"$out": "rentals_per_month"}` and delete a month's rentals: with `$out` the month disappears, with `$merge` its old document stays.
- Fire ten report requests at once and count the status codes:

  ```bash
  seq 10 | xargs -P 10 -I{} curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/reports/monthly/2023-03 | sort | uniq -c
  ```

- Change a payment in PostgreSQL for July 2022 and read the report again: it does not change. That is the point of a frozen report.
- Drop the `films` collection of `s14_fastapi` in `mongosh`, then bring it back from the newest backup into the original database. This is the tutorial's command plus `--nsInclude`; only run it against your own database:

  ```bash
  # from the repository root
  docker compose exec -T mongo mongorestore --uri "mongodb://root:change-me-mongo@localhost:27017/?authSource=admin" \
      --nsInclude 's14_fastapi.films' --archive --gzip --drop < sessions/14-mongodb-pipelines/fastapi/backups/<file>.archive.gz
  ```

  Without `--nsInclude`, `--drop` replaces every collection in the archive. `monthly_reports` goes back to the state of the backup, so a report created after it (such as `2023-03` above) disappears.
