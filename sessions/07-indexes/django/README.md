# Session 07 in Django: indexes and query plans

The session 07 tutorial on a copy of Pagila: build `big_rental` with 2 million rows, read `EXPLAIN (ANALYZE, BUFFERS)` before and after a composite, a partial and an expression index, and measure what the indexes cost on writes.

| File | What it shows |
|------|---------------|
| `demo/models.py` | The three tutorial indexes declared in `Meta.indexes`: `fields=["customer_id", "-rented_at"]` (composite with `DESC`), `condition=Q(returned_at__isnull=True)` (partial) and `Index(Lower("email"))` (expression), plus a plain index on `rented_at` that the planner ignores when most rows match. |
| `demo/indexes.py` | Builds and drops those indexes with `connection.schema_editor()`, and prints the SQL Django generates for each. |
| `demo/views.py` | `GET /explain/<name>` runs `EXPLAIN (ANALYZE, BUFFERS)` with `QuerySet.explain(analyze=True, buffers=True)` and returns the plan and the execution time; `?force_index=1` turns off sequential and bitmap scans for that one query. `GET /indexes` lists the tutorial indexes that exist. |
| `demo/management/commands/make_big_rental.py` | The tutorial's `setseed(0.1)` + `generate_series` table; `--rows` changes the size. |
| `demo/management/commands/index.py` | `index create|drop|list [name|all]`. |
| `demo/management/commands/write_cost.py` | Times the tutorial's 100,000-row `INSERT` without and with the two `big_rental` indexes, then puts the indexes back as they were. |

What Django can and cannot express here:

- All three indexes can be declared in Django, including `DESC`, the partial `WHERE` and the `lower(email)` expression. Normally `makemigrations` would turn them into `AddIndex` operations. Both models are `managed = False` (`big_rental` is created by a command and `customer` belongs to Pagila), and Django writes no index operations for unmanaged models, so the `index` command applies them with the schema editor. That also lets you drop and recreate them while you compare plans.
- `CREATE TABLE big_rental AS SELECT ... generate_series(...)` has no ORM equivalent and is plain SQL in the command.
- `QuerySet.explain()` only works on a queryset. The `open-rentals` query is a `count(*)`, and `.count()` runs straight away, so its `EXPLAIN` is plain SQL with a parameter.
- On a live table you would use `CREATE INDEX CONCURRENTLY`. In migrations Django has `AddIndexConcurrently` in `django.contrib.postgres.operations` (the migration must set `atomic = False`).
- `email__iexact` is written as `UPPER(email) = UPPER(...)`, so an index on `lower(email)` does not help it. Filter on `alias(email_lower=Lower("email"))` instead, or index `Upper("email")`.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s07_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py make_big_rental   # about 100 MB
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Before the indexes:

```bash
curl localhost:8001/explain/customer-latest        # Parallel Seq Scan + Sort
curl localhost:8001/explain/open-rentals
curl localhost:8001/explain/customer-email
curl localhost:8001/explain/customer-email-iexact
```

Create the indexes and run the same calls again:

```bash
uv run python manage.py index create all
curl localhost:8001/explain/customer-latest        # Index Scan using big_rental_customer_rented, no Sort
curl localhost:8001/explain/open-rentals           # Index Only Scan using big_rental_open
curl localhost:8001/explain/customer-email         # Index Scan using customer_lower_email
curl localhost:8001/explain/customer-email-iexact  # still a Seq Scan
curl localhost:8001/explain/recent-rentals                  # Seq Scan, although big_rental_rented exists
curl 'localhost:8001/explain/recent-rentals?force_index=1'  # Index Scan using big_rental_rented, forced
curl 'localhost:8001/explain/recent-rentals?days=7'         # Bitmap Index Scan on big_rental_rented
uv run python manage.py write_cost
uv run python manage.py index drop all
```

On the machine this was tested on, `customer-latest` went from about 40 ms to under 0.1 ms, `open-rentals` from about 30 ms to about 5 ms, and the 100,000-row `INSERT` went from about 30 ms to about 100 ms with the two indexes.

`recent-rentals` is the index the planner does not use. It asks for the rentals of the last `?days=` days (730 by default): 1,334,083 of the 2,000,000 rows. The planner reads the whole table, about 130 ms and 12,712 buffers, each page once. `force_index=1` shows the plan it rejected: the index is in date order, the rows are stored in no particular order, so almost every row means a jump to another page. That came to about 1,337,000 buffers and 570 ms. With `days=7` only 13,000 rows match and the same index is used, in about 8 ms. `write_cost` leaves `big_rental_rented` out of both measurements.

## Things to try

- Record each case as in the tutorial: query, plan before, index, plan after, times, one sentence explaining the difference.
- Run each `EXPLAIN` twice. Compare `Buffers: shared read` (from disk) on the first run with `shared hit` (from memory) on the second.
- With the indexes, `open-rentals` becomes an `Index Only Scan using big_rental_open`. Compare the size of the two indexes on `big_rental` (`SELECT relname, pg_size_pretty(pg_relation_size(oid)) FROM pg_class WHERE relname LIKE 'big_rental_%';`). Why is the partial index so much smaller?
- Drop `big_rental_customer_rented` and create `models.Index(fields=["rented_at", "customer_id"], name="big_rental_wrong_order")` instead (add it to `Meta.indexes` first). Does `customer-latest` use it?
- Run `uv run python manage.py make_big_rental --rows 200000` (it drops the table and its indexes) and repeat the before and after. How much of the difference was down to the table size?
- Run `uv run python manage.py write_cost --rows 500000` with `customer_lower_email` present and absent. Why does it make no difference?
