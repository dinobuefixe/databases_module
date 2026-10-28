# Session 14 in Django: aggregation pipelines and a frozen report

The session 14 tutorial with Django and `pymongo`: a loader that builds the `films` and `customers` collections from Pagila, one endpoint per tutorial pipeline (`$group`, `$unwind`, `$dateTrunc`, `$bucket`, `$facet`, `$lookup`, `$match` early and late, `$merge`), a monthly report generated once from PostgreSQL and then refused on the second attempt, and `mongodump` / `mongorestore` commands for this project's database only.

| File | What it shows |
|------|---------------|
| `demo/models.py` | The Pagila tables the loader and the report read, unmanaged. `film_actor`, `film_category` and `payment` use `CompositePrimaryKey`. |
| `demo/management/commands/load_documents.py` | `films` with `length`, the list of `categories` and the cast embedded, `rental_rate` as `Decimal128`; `customers` with `store_id`, `rentals_total` and the 10 most recent rentals, picked in one query with `Window(RowNumber())`; an index on `recent_rentals.rental_date`. |
| `demo/pipelines.py` | The pipelines: films per rating with the average rate, top actors with `$unwind`, rentals per month with `$dateTrunc`, customers by activity with `$bucket`, a customers summary with `$facet`, the latest rentals with `$lookup`, `$match` late and early with `explain`, and rentals per month materialised with `$merge`. |
| `demo/reports.py` | The frozen report: payments per store for one month, read through the `readonly` connection and inserted with `_id` = `"YYYY-MM"`. |
| `demo/views.py` | One endpoint per pipeline (below), `POST` and `GET /reports/rentals-per-month`, `POST` and `GET /reports/monthly/{YYYY-MM}`. |
| `demo/management/commands/mongo_backup.py`, `mongo_restore.py` | `mongodump --archive --gzip` into `backups/` (git-ignored, written to a `.part` file and renamed only on success), and `mongorestore` into `s14_django_restored` with a count check. |
| `demo/clients.py` | `container_mongo_url()`: the URL the backup commands use inside the `mongo` container. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s14_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate            # records the unmanaged models, creates no tables
uv run python manage.py load_documents
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl localhost:8001/films/per-rating
curl 'localhost:8001/actors/top?limit=10'
curl localhost:8001/rentals/per-month
curl localhost:8001/customers/by-activity       # $bucket on rentals_total
curl localhost:8001/customers/summary           # $facet: per store and the 3 most active
curl localhost:8001/rentals/latest              # $lookup the film of the 5 latest rentals
curl localhost:8001/rentals/match-position      # docs_examined: 999 with $match late, 164 early
curl -X POST localhost:8001/reports/rentals-per-month   # {"months": 26, "rentals": 9622}, the same every time
curl localhost:8001/reports/rentals-per-month
curl -X POST localhost:8001/reports/monthly/2022-07     # 201
curl -X POST localhost:8001/reports/monthly/2022-07     # 409, already frozen
curl localhost:8001/reports/monthly/2022-07
```

Backup and restore. `mongodump` and `mongorestore` run inside the `mongo` container, where the server is `localhost:27017` whatever port your machine publishes, so the commands log in with the root user from the `.env` at the root of the repository instead of `MONGO_URL`:

```bash
uv run python manage.py mongo_backup
uv run python manage.py mongo_restore      # newest archive in backups/ into s14_django_restored
```

The tutorial's restore command uses `--drop` without a namespace filter, which replaces every collection in the archive's databases. Here the archive only contains `s14_django`, and `--nsFrom`/`--nsTo` send it to `s14_django_restored`, so the original is never touched. To restore over the original in your own environment, remove `--nsFrom`/`--nsTo`.

## Notes

- **`$lookup` sparingly.** `rentals/latest` reads the film's rating and categories from `films` with `$lookup`, after `$limit`, so it looks up 5 films. If most queries need the rating next to a rental, copy it into `recent_rentals` in the loader instead: a join on every read is a sign the data is relational or should be embedded.
- **`$match` first.** In `rentals/match-position` both pipelines return the same numbers. The late `$match` filters array elements after `$unwind`, so MongoDB cannot move it earlier and reads all 999 customers. The early one keeps only customers with a rental in the range, uses the index on `recent_rentals.rental_date`, and reads 164.
- **`$merge` is idempotent here.** The `_id` of each document is the month, and `whenMatched: "replace"` overwrites the document for a month that already exists. Run it twice and `rentals_per_month` has the same 26 documents. `$out` would also work, but it replaces the whole collection on every run.

## Things to try

- `rentals/per-month` only counts the 10 rentals embedded per customer, so it starts in 2024 even though Pagila has rentals from 2022. Compare it with `SELECT date_trunc('month', rental_date), count(*) FROM rental GROUP BY 1` and decide which engine should answer this question.
- Add `{"$round": ["$avg_rate", 2]}` in a `$set` stage after the `$group` in `films_per_rating`.
- Correct one payment of July 2022 in PostgreSQL (`UPDATE payment SET amount = amount + 1 WHERE ...`), then `GET` the report: it still shows the old revenue. That is what frozen means.
- Put a `$match` on `rating` before the `$group` in `films_per_rating`, and a `$match` on `_id` after it, and compare them with `pipelines.docs_examined("films", [...])` in `uv run python manage.py shell`. Both read the same documents: MongoDB moves a `$match` on the group key before `$group` for you. It cannot do that in `match_position`, because there the filter is on the elements that `$unwind` produces.
- Use the `readonly` role from session 09 for the report. Give it read access to this database (`docker compose exec postgres psql -U postgres s14_django -c 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly'` from the repository root), set `READONLY_DATABASE_URL=postgresql://readonly:change-me-readonly@localhost:5432/s14_django` and restart the server. The report still works; try to make `build_monthly_report` write something and PostgreSQL refuses it with `permission denied`.
