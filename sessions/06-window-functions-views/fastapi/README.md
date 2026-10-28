# Session 06 in FastAPI: window functions and views

The session 06 tutorial on a copy of Pagila: `DENSE_RANK` for the longest films per rating, a running total with `SUM ... OVER`, gaps between rentals with `LAG`, and the `daily_rentals` materialised view with `REFRESH ... CONCURRENTLY`.

| File | What it shows |
|------|---------------|
| `sql/longest_per_rating.sql` | `DENSE_RANK() OVER (PARTITION BY rating ORDER BY length DESC)` in a CTE, filtered outside because a window function cannot go in `WHERE`. |
| `sql/running_total.sql` | `SUM(amount) OVER (PARTITION BY customer_id ORDER BY payment_date)` for one customer. |
| `sql/rental_gaps.sql` | `rental_date - LAG(rental_date) OVER (...)`: the interval since the previous rental. |
| `sql/001_daily_rentals.sql` | The materialised view and the unique index that `CONCURRENTLY` needs. |
| `scripts/create_views.py` | Applies `001_daily_rentals.sql`. Safe to run again. |
| `app/main.py` | `GET /films/longest-per-rating?top=2`, `GET /customers/{id}/running-total`, `GET /customers/{id}/rental-gaps`, `GET /daily-rentals`, `POST /daily-rentals/refresh`. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s06_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.create_views
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
curl localhost:8000/films/longest-per-rating
curl 'localhost:8000/films/longest-per-rating?top=1'
curl localhost:8000/customers/1/running-total
curl localhost:8000/customers/1/rental-gaps
curl 'localhost:8000/daily-rentals?limit=7'
curl 'localhost:8000/daily-rentals?start=2022-05-24&end=2022-05-31'
curl -X POST localhost:8000/daily-rentals/refresh
curl -X POST 'localhost:8000/daily-rentals/refresh?concurrently=false'
```

With `top=2` the response has more than two films per rating: three G films tie at 185 minutes and share position 1, and the next length (184) is position 2.

## Things to try

Open `psql` on the project's database from the repository root with `docker compose exec postgres psql -U postgres -d s06_fastapi`, then:

- In `sql/longest_per_rating.sql`, replace `DENSE_RANK` with `RANK` and then with `ROW_NUMBER`, and call the endpoint again. `RANK` leaves a gap after ties (1, 1, 1, 4), so position 2 may not exist. `ROW_NUMBER` cuts tied films at random.
- Remove `ORDER BY payment_date` from inside `OVER` in `sql/running_total.sql`. Without an order, the frame is the whole partition and every row shows the customer's grand total.
- Swap `LAG` for `LEAD` in `sql/rental_gaps.sql`: the gap now points forward, so it is negative (`rental_date` minus a later date), and the last rental gets `NULL`.
- See that the materialised view is stale. Insert a rental for today: `INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id) VALUES (now(), 1, 1, 1);` Then `GET /daily-rentals?limit=1` does not show today until you call `POST /daily-rentals/refresh`.
- Drop the unique index (`DROP INDEX daily_rentals_day;`) and call the refresh with `concurrently=true`. The API answers 409 with PostgreSQL's error and hint. Run `uv run python -m scripts.create_views` to put the index back.
- In one `psql` session run `BEGIN; REFRESH MATERIALIZED VIEW daily_rentals;` without committing. In a second session, `SELECT count(*) FROM daily_rentals;` waits. Repeat with `CONCURRENTLY`: the second session reads the old rows straight away. `ROLLBACK` the first session when done.
