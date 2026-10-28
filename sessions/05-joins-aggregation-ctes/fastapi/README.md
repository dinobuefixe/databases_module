# Session 05 in FastAPI: joins, aggregation and CTEs

The ten questions from the session 05 tutorial, one endpoint each. The SQL lives in `sql/` exactly as in the tutorial, and each response includes the SQL text next to the rows.

| File | What it shows |
|------|---------------|
| `sql/rentals_per_staff.sql` | Two `JOIN`s and `GROUP BY`: rentals handled by each staff member, per store. |
| `sql/customers_over_40.sql` | `HAVING` filters groups after counting. The threshold is a parameter (`%(min_rentals)s`), 40 by default. |
| `sql/rentals_per_customer.sql` | `LEFT JOIN` keeps customers with no rentals. Returns `count(r.rental_id)` and `count(*)` side by side: 0 and 1 for those customers. |
| `sql/films_without_inventory.sql` | Anti-join with `NOT EXISTS`: films with no copy in any store. |
| `sql/customers_without_rentals.sql` | Anti-join with `LEFT JOIN ... WHERE r.rental_id IS NULL`: customers who never rented. |
| `sql/duplicate_customer_names.sql` | Self join: `customer` twice, pairs of customers with the same first and last name. |
| `sql/films_longer_than_average.sql` | Subquery in `WHERE` that runs once: films longer than the average film. |
| `sql/films_above_rating_average.sql` | Correlated subquery: films longer than the average of their own rating. |
| `sql/customer_totals.sql` | Subqueries in `FROM`: rentals and payments aggregated separately, then joined, so the 1:N joins do not multiply the rows. |
| `sql/customers_above_average.sql` | Two CTEs built in steps: total per customer, the average of those totals, then the comparison. |
| `app/main.py` | `GET /questions/...`, one per file. Each returns `sql`, `row_count` and `rows`. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s05_fastapi --pagila
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
curl localhost:8000/questions/rentals-per-staff
curl localhost:8000/questions/customers-over-40
curl 'localhost:8000/questions/customers-over-40?min_rentals=60'
curl localhost:8000/questions/rentals-per-customer
curl localhost:8000/questions/films-without-inventory
curl localhost:8000/questions/customers-without-rentals
curl localhost:8000/questions/duplicate-customer-names
curl localhost:8000/questions/films-longer-than-average
curl localhost:8000/questions/films-above-rating-average
curl localhost:8000/questions/customer-totals
curl localhost:8000/questions/customers-above-average
```

On a fresh copy of the course's Pagila the row counts are, in that order, 2, 669, 999, 42, 2, 20, 489, 497, 999 and 592.

## Things to try

Open `psql` on the project's database from the repository root with `docker compose exec postgres psql -U postgres -d s05_fastapi`, then:

- Build `rentals_per_staff.sql` one join at a time and check the row count after each step: `SELECT count(*) FROM rental;`, then with the `staff` join, then with the `store` join. The count should not change, because each rental has exactly one staff member and each staff member one store.
- In `customers_over_40.sql`, move `count(*) > 40` from `HAVING` to `WHERE`. Read the error: aggregates are not allowed in `WHERE`, because it runs before the groups exist.
- Rewrite `films_without_inventory.sql` as `LEFT JOIN inventory i ON i.film_id = f.film_id WHERE i.inventory_id IS NULL`. You should get the same 42 films. Compare both plans with `EXPLAIN`.
- Try the `NOT IN` version: `WHERE f.film_id NOT IN (SELECT film_id FROM inventory)`. It works here because `inventory.film_id` is `NOT NULL`. Add `UNION SELECT NULL` to the subquery and it returns no rows at all.
- In `rentals_per_customer.sql`, change `LEFT JOIN` to `JOIN`. You get 997 rows instead of 999: customers 647 and 978 disappear. Then drop the `GROUP BY` and the counts and count the joined rows: 51,805 with `JOIN`, 51,807 with `LEFT JOIN`.
- In `customers_without_rentals.sql`, change `WHERE r.rental_id IS NULL` to `IS NOT NULL`. You get 51,805 rows, one per rental, with every customer repeated: a join along 1:N repeats the "1" side. `SELECT DISTINCT` brings it to 997.
- In `duplicate_customer_names.sql`, change `c2.customer_id > c1.customer_id` to `<>` (40 rows, each pair twice), then remove it (1,039 rows, each customer also paired with itself).
- Run `EXPLAIN` on `films_longer_than_average.sql` and on `films_above_rating_average.sql`. The first runs the subquery once (`InitPlan`); the correlated one runs it per film (`SubPlan`). Remove `WHERE f2.rating = f.rating` and you are back to 489 films.
- Write `customer_totals.sql` the wrong way, joining `rental` and `payment` straight to `customer` and grouping by customer. Customer 1 goes from 66 rentals and 217.35 paid to 4,290 and 14,345.10: 66 rentals times 65 payments.
- Run `EXPLAIN` on `customers_above_average.sql`. The plan has no separate step for the `average` CTE name: PostgreSQL inlines simple CTEs. `spend` is used twice, so it is computed once and reused.
