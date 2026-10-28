# Session 06 in Django: window functions and a materialised view

The session 06 tutorial on a copy of Pagila: the longest films per rating with `DENSE_RANK`, a customer's running total of payments, the gaps between a customer's rentals with `LAG`, and the `daily_rentals` materialised view with a refresh endpoint.

| File | What it shows |
|------|---------------|
| `demo/views.py` | `Window(DenseRank(), partition_by=..., order_by=...)`, `Window(Sum("amount"), ...)` and `Window(Lag("rental_date"), ...)`, each response with the SQL Django generated. |
| `demo/models.py` | Pagila tables with `managed = False`, and `DailyRental`, an unmanaged model over the materialised view so it can be queried with the ORM. |
| `demo/migrations/0002_daily_rentals_view.py` | Hand-written `RunSQL` with the tutorial's `CREATE MATERIALIZED VIEW` and the unique index, plus the reverse SQL. Django has no operation for materialised views. |

Two things Django does for you:

- **Filtering on a window function.** SQL does not allow a window function in `WHERE`. When you `filter()` on a window annotation (`pos__lte=2`), Django wraps the query in a subquery named `qualify` and filters outside it, which is what the tutorial does with a CTE. Look at the `sql` field of `/films/longest-per-rating`.
- **Expressions over a window.** `F("rental_date") - Window(Lag("rental_date"), ...)` becomes `rental_date - LAG(rental_date) OVER (...)`. Django returns the `interval` as a `timedelta`, which `JsonResponse` writes as an ISO 8601 duration (`P2DT23H04M46S`).

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s06_django --pagila
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
curl 'localhost:8001/films/longest-per-rating?top=2'     # 22 rows: ties share a position
curl localhost:8001/customers/1/running-total
curl localhost:8001/customers/1/rental-gaps
curl 'localhost:8001/daily-rentals?from=2022-05-24&to=2022-05-31'
curl -X POST localhost:8001/daily-rentals/refresh
```

## Things to try

- Change `DenseRank()` to `Rank()` and then to `RowNumber()` (from `django.db.models.functions`) and compare the number of rows for `top=2`.
- Add `frame=RowRange(start=None, end=0)` to the running total's `Window` and compare `/customers/23/running-total` before and after: customer 23 has two payments at the same `payment_date` (2026-07-28). The default frame (`RANGE`) gives tied rows the same total.
- See the view go stale. In `psql` (`docker compose exec postgres psql -U postgres -d s06_django`):

  ```sql
  INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id)
  SELECT '2030-01-01 10:00+00', 1, 1, min(staff_id) FROM staff;
  ```

  `GET /daily-rentals?from=2030-01-01` returns nothing until you call `POST /daily-rentals/refresh`. Delete the row and refresh again afterwards.
- Drop the unique index (`DROP INDEX daily_rentals_day;`) and call the refresh endpoint: `CONCURRENTLY` refuses to run and the response (409) carries PostgreSQL's hint. Recreate it with `CREATE UNIQUE INDEX daily_rentals_day ON daily_rentals (day);`.
- Run `uv run python manage.py migrate demo 0001` and check that the view is gone, then `uv run python manage.py migrate` to create it again.
