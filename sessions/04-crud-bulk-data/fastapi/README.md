# Session 04 in FastAPI: CRUD, upsert and bulk data

The session 04 tutorial on a copy of Pagila: filtered reads, `INSERT ... RETURNING`, a safe `UPDATE` checked against an expected row count, an upsert, and bulk loads timed three ways.

| File | What it shows |
|------|---------------|
| `sql/001_tables.sql` | `film_views` (target of the upsert) and `person` (target of the bulk load). Created when the app starts. |
| `app/main.py` | `GET /films` with rating, title search (`ILIKE`), sort, `LIMIT` and `OFFSET`. `POST /actors` returns the generated `actor_id`. `POST /films/rental-rate` counts, updates in a transaction and rolls back if the count is not the one you expected. `POST /films/{id}/views` is the upsert. |
| `scripts/bulk_load.py` | `person`: 100,000 Faker rows (seed 42) loaded with `COPY`, with `executemany` and with one `INSERT` per row, with timings. `reading`: 1,000,000 rows built in SQL with `generate_series` and `setseed`. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s04_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
# the tutorial's SELECT: rating R, title contains "love", longest first
curl 'localhost:8000/films?rating=R&q=love&sort=length&order=desc&limit=10'
curl 'localhost:8000/films?sort=length&order=desc&limit=5&offset=5'

curl -X POST localhost:8000/actors -H 'content-type: application/json' \
  -d '{"first_name": "Ada", "last_name": "Lovelace"}'

# safe update: the WHERE matches 73 films on a fresh copy of Pagila
curl -X POST localhost:8000/films/rental-rate -H 'content-type: application/json' \
  -d '{"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 70}'                   # 409, nothing changed
curl -X POST localhost:8000/films/rental-rate -H 'content-type: application/json' \
  -d '{"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 73, "dry_run": true}'  # runs, then ROLLBACK
curl -X POST localhost:8000/films/rental-rate -H 'content-type: application/json' \
  -d '{"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 73}'                   # COMMIT

# upsert: run it twice and watch views go from 1 to 2
curl -X POST localhost:8000/films/1/views
curl -X POST localhost:8000/films/1/views
```

Bulk data:

```bash
uv run python -m scripts.bulk_load person                   # 100,000 rows, three methods
uv run python -m scripts.bulk_load person --rows 500000 --methods copy,executemany
uv run python -m scripts.bulk_load reading                  # 1,000,000 rows with generate_series
```

On a laptop the `person` run printed about 0.2 s for `COPY`, 0.6 s for `executemany` and 20 s for one `INSERT` per row. Your numbers will differ; the ratio is the lesson.

## Things to try

- Run `uv run python -m scripts.bulk_load reading` twice. `sum(value)` is the same both times because `setseed(0.42)` fixes the sequence of `random()` values. Remove the `setseed` line and run it again.
- Run the safe update a second time with `"expected": 73`. The `WHERE` now matches 0 rows, so it is refused. To get the original data back, recreate the database with `./scripts/create-db.sh s04_fastapi --pagila --reset`.
- In `app/main.py` the sort column comes from a fixed list and is quoted with `sql.Identifier`, while values travel as `%s` parameters. Why can a column name not be a parameter? Session 09 shows what happens when user input is pasted into SQL.
- The one-`INSERT`-per-row load runs in a single transaction. In `person()` in `scripts/bulk_load.py`, open the connection with `pg_connect(autocommit=True)` so that every row commits on its own, and time `--rows 10000 --methods insert` again.
- Call `POST /films/99999/views`. The foreign key on `film_views.film_id` refuses it and the API answers 404.
