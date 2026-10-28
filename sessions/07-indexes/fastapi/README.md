# Session 07 in FastAPI: indexes and optimisation

The session 07 tutorial on a copy of Pagila: a 2,000,000-row `big_rental` table, `EXPLAIN (ANALYZE, BUFFERS)` before and after a composite, a partial and an expression index, and the cost those indexes add to every `INSERT`.

| File | What it shows |
|------|---------------|
| `scripts/create_big_rental.py` | Builds `big_rental` with `generate_series` and `setseed(0.1)` (row count configurable), then runs `VACUUM ANALYZE`. The tutorial runs `ANALYZE` only; the `VACUUM` does now what autovacuum would do a minute later, so the plans are the same on every run. |
| `app/indexes.py` | The three tutorial indexes declared with SQLAlchemy `Index` and compiled to PostgreSQL DDL. |
| `scripts/indexes.py` | `create` or `drop` one index (`composite`, `partial`, `expression`) or `all`; `list` prints the DDL. |
| `app/queries.py` | The tutorial queries and a helper that runs them under `EXPLAIN (ANALYZE, BUFFERS)`. |
| `app/main.py` | `GET /explain/{name}` returns the plan text, planning and execution time; `?force_index=1` turns off sequential and bitmap scans for that one query. `GET /indexes` shows which tutorial indexes exist and their size. |
| `scripts/write_cost.py` | Times the tutorial's 100,000-row `INSERT` with no tutorial index, with each one and with both, rolling back each time. |

The rest of the project uses plain SQL with `psycopg`. SQLAlchemy appears only in `app/indexes.py`, to show that all three tutorial indexes can be declared next to the table instead of written by hand: the sort direction with `.desc()`, the partial index with `postgresql_where`, the expression index with `func.lower(...)`. None of them needs raw SQL. What SQLAlchemy cannot declare is the `CREATE TABLE ... AS SELECT` that builds `big_rental`, so that stays as SQL in the script.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s07_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.create_big_rental          # about 100 MB, a few seconds
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Before any index:

```bash
curl localhost:8000/explain/customer_latest
curl localhost:8000/explain/open_overdue
curl localhost:8000/explain/customer_email
curl localhost:8000/indexes
```

Look for `Seq Scan` (or `Parallel Seq Scan`), `execution_ms` and `Buffers: shared read`. Then create the indexes and call the same endpoints again:

```bash
uv run python -m scripts.indexes create composite
uv run python -m scripts.indexes create partial
uv run python -m scripts.indexes create expression
curl localhost:8000/explain/customer_latest
curl 'localhost:8000/explain/customer_latest?customer_id=7'
curl localhost:8000/explain/open_overdue
curl 'localhost:8000/explain/customer_email?email=MARY.SMITH@sakilacustomer.org'
uv run python -m scripts.write_cost
```

On a laptop, `customer_latest` went from about 30 ms (parallel sequential scan and sort) to under 0.1 ms (index scan, no sort), and `open_overdue` from about 23 ms to 5 ms (index only scan on the 1.3 MB partial index). The write cost went from about 20 ms per 100,000 rows to 90 ms with both indexes.

An index the planner does not use. `recent_rentals` asks for every rental of the last `days` days (730 by default). Create a plain index on `rented_at` and compare:

```bash
uv run python -m scripts.indexes create single
curl localhost:8000/explain/recent_rentals                   # Seq Scan: the index is ignored
curl 'localhost:8000/explain/recent_rentals?force_index=1'   # Index Scan, forced
curl 'localhost:8000/explain/recent_rentals?days=7'          # Bitmap Index Scan on big_rental_rented
uv run python -m scripts.indexes drop single
```

With 730 days, 1,334,083 of the 2,000,000 rows match, and the planner reads the whole table: about 170 ms and 12,736 buffers, each page once. With `force_index=1` the index is walked in date order, which has nothing to do with the order the rows are stored in, so almost every row means a jump to another page: about 1,337,000 buffers and 470 ms. With `days=7` only 13,000 rows match and the same index is used, in about 6 ms. Drop the index when you are done: without the composite index, `customer_latest` walks `big_rental_rented` backwards instead of scanning the table, which changes its "before" plan.

## Things to try

- Record each case as the tutorial asks: query, plan before, index, plan after, times, and one sentence explaining the difference.
- Drop the composite index and create one on `(rented_at DESC, customer_id)` instead. Run `customer_latest` again: the index is still used, but it is walked in date order and `customer_id` is checked on every entry until ten rows match, so `Buffers` goes up from about 16 to about 50. Then try `?customer_id=1000`, a customer with no rentals: the whole index is read (about 7,600 buffers, 30 ms), where the composite index answers from 3 buffers.
- `customer_email` on 999 customers takes well under a millisecond even without the index, because the whole table fits in 32 pages. Indexes pay off on big tables; on small ones the planner may prefer a sequential scan anyway.
- Write `WHERE email = 'MARY.SMITH@sakilacustomer.org'` (no `lower`) in `psql` and run `EXPLAIN`. The expression index is not used, because the query does not use the same expression.
- Run `EXPLAIN ANALYZE SELECT count(*) FROM big_rental WHERE returned_at IS NOT NULL;`. 97% of rows match, so an index would not help.
- `write_cost` inserts rows with `returned_at = NULL`, so every new row also goes into the partial index. Change the `INSERT` to use `now()` for `returned_at` and see the partial index cost almost disappear.
- `pg_stat_statements` is loaded in this setup. After calling the endpoints a few times, run `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` and `SELECT calls, round(total_exec_time) AS ms, query FROM pg_stat_statements WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database()) AND query LIKE '%big_rental%' ORDER BY total_exec_time DESC LIMIT 5;` The view covers every database on the server, hence the `dbid` filter.
