# Session 11 in FastAPI: SQLAlchemy and the N+1 problem

Maps Pagila's `customer` and `rental` tables with SQLAlchemy 2.0, lists customers with their rental count with lazy and with eager loading, and reports how many SQL queries each request ran.

| File | What it shows |
|------|---------------|
| `app/models.py` | `DeclarativeBase`, `Mapped`, `mapped_column` and the two sides of `relationship()` between `Customer` (1) and `Rental` (N). |
| `app/db.py` | The engine with `echo=True`, a session per request (`get_session`), and a `before_cursor_execute` event listener that counts the statements sent to PostgreSQL. |
| `app/main.py` | `GET /customers?eager=false\|true` (N+1 vs `selectinload`), `GET /customers/top` (aggregation in the ORM), `GET /rentals/recent?eager=false\|true` (N:1 with `joinedload`). |
| `scripts/n_plus_one.py` | The tutorial script: the three blocks, each in its own session, with the query count of each. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s11_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.n_plus_one
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8000/customers?limit=20'               # "queries": 21
curl 'localhost:8000/customers?limit=20&eager=true'    # "queries": 2
curl 'localhost:8000/customers/top?limit=5'            # one query with GROUP BY
curl 'localhost:8000/rentals/recent?limit=10'          # 1 + one per distinct customer
curl 'localhost:8000/rentals/recent?limit=10&eager=true'  # 1, with a JOIN
```

## Reading the SQL log

With `SQL_ECHO=true` in `.env`, the engine is created with `echo=True` and every statement appears in the uvicorn terminal with its parameters. For `GET /customers?limit=20` you will see one `SELECT ... FROM customer ... LIMIT` followed by twenty `SELECT ... FROM rental WHERE %(param_1)s::INTEGER = rental.customer_id`, one per customer. With `eager=true` the second statement becomes a single `SELECT ... FROM rental WHERE rental.customer_id IN (...)` with all twenty ids.

The `queries` field in each response comes from the event listener in `app/db.py`, so you can compare the two versions without counting log lines.

## Things to try

- Change `limit` to 200 and compare the response time of `eager=false` and `eager=true`. The gap grows with the number of rows.
- In `/rentals/recent` without `eager`, the count can be lower than 1 + `limit`: when two rentals belong to the same customer, the session already holds that `Customer` (the identity map) and does not query it again.
- Swap `selectinload` for `joinedload` in `/customers`. SQLAlchemy raises `InvalidRequestError: The unique() method must be invoked on this Result`: the `JOIN` repeats each customer row once per rental. Add `.unique()` before `.all()` and it works, with one query, but look at the log: the `LIMIT` moves into a subquery and about 1,400 rows travel back for 20 customers. That is why `joinedload` suits N:1 better than collections.
- Pagila has no index on `rental.customer_id`. Run `EXPLAIN ANALYZE SELECT * FROM rental WHERE customer_id = 1;` in `psql` and think about what that means for twenty lazy loads.
- Set `SQL_ECHO=false` in `.env` and run `uv run python -m scripts.n_plus_one` to see only the counts.
