# Session 04 in Django: CRUD, upsert and bulk data

The session 04 tutorial on a copy of Pagila: filtered reads, `INSERT ... RETURNING`, an update that rolls back when the row count is not the expected one, an upsert, and bulk loads timed with `COPY`, `bulk_create` and one `INSERT` per row.

| File | What it shows |
|------|---------------|
| `demo/models.py` | `Film` and `Actor` mapped to Pagila with `managed = False`. `FilmViews` and `Person` are new tables created by the migration. |
| `demo/views.py` | `GET /films` with filters, sort and pagination. `POST /actors` (Django sends `INSERT ... RETURNING actor_id, last_update`). `POST /films/rental-rate`, the safe update. `POST /films/<id>/views`, the upsert in SQL. Each response includes the SQL Django ran. |
| `demo/management/commands/load_people.py` | Generates people with Faker (seed 42) and loads them with `COPY`, `bulk_create` and `Person.objects.create()` per row, printing the time of each. |
| `demo/management/commands/make_readings.py` | The tutorial's `setseed` + `generate_series` table `reading`, with a checksum to show the data is the same on every run. |

Where the ORM differs from the tutorial SQL:

- `title__icontains="love"` is written as `UPPER(title) LIKE UPPER('%love%')`, not `ILIKE`. Same result; it matters for indexes in session 07.
- `QuerySet.update()` returns the row count but not the rows (no `RETURNING`). The safe update first selects the rows with `select_for_update()` so the list in the response is exactly what was changed.
- `bulk_create(update_conflicts=True)` can only write `SET views = EXCLUDED.views`, which replaces the value. Adding 1 to the stored value needs the SQL upsert, sent through `connection.cursor()` with a parameter.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s04_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8001/films?rating=R&q=love&sort=-length&limit=10'
curl 'localhost:8001/films?sort=title&limit=5&offset=20'
curl -X POST localhost:8001/actors -H 'content-type: application/json' -d '{"first_name": "Ada", "last_name": "Lovelace"}'

# Safe update: a dry run first (73 rows on a fresh copy of Pagila) ...
curl -X POST localhost:8001/films/rental-rate -H 'content-type: application/json' -d '{"rating": "NC-17", "below": 1}'
# ... a wrong expected count is rolled back (409) ...
curl -X POST localhost:8001/films/rental-rate -H 'content-type: application/json' -d '{"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 3}'
# ... and the right one is committed.
curl -X POST localhost:8001/films/rental-rate -H 'content-type: application/json' -d '{"rating": "NC-17", "below": 1, "new_rate": 1.99, "expected": 73}'

# Upsert: run it twice and views goes from 1 to 2.
curl -X POST localhost:8001/films/1/views
curl -X POST localhost:8001/films/1/views
```

Bulk data:

```bash
uv run python manage.py make_readings      # 1,000,000 rows, sum(value) = 49998115.71 every time
uv run python manage.py load_people        # 100,000 people with each method
uv run python manage.py load_people --rows 500000 --method copy
```

On the machine this was tested on, 100,000 rows took about 0.1 s with `COPY`, 0.8 s with `bulk_create` and 24 s with one `INSERT` per row.

## Things to try

- Run `make_readings` twice and compare the `sum(value)`. Remove the `setseed` line and run it again.
- Put the loop in `load_insert` inside `transaction.atomic()` and run `load_people --method insert` again. Here it saved only about 15%: most of the time goes on one network round trip per row, which `bulk_create` and `COPY` avoid by sending many rows per message.
- Change `batch_size` in `load_bulk_create` to 100 and to 50,000 and compare.
- Look at the SQL returned by `POST /films/rental-rate` with a wrong count: `BEGIN`, `SELECT ... FOR UPDATE`, `UPDATE`, `ROLLBACK`.
- Write the upsert with `FilmViews.objects.bulk_create([FilmViews(film_id=1, views=1)], update_conflicts=True, unique_fields=["film"], update_fields=["views"])` in `uv run python manage.py shell`, run it twice and read `FilmViews.objects.get(pk=1).views` after each: the 2 from the API calls is replaced by 1, and it stays at 1.
