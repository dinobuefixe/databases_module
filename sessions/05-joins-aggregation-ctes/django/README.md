# Session 05 in Django: joins, aggregation and CTEs

The ten questions from the session 05 tutorial, each answered with the Django ORM and with the tutorial's SQL. Both return the same rows, and every response shows the SQL that was sent to PostgreSQL.

| File | What it shows |
|------|---------------|
| `demo/models.py` | The Pagila tables the questions need, with `managed = False` and foreign keys so the ORM can follow `rental -> staff -> store`. |
| `demo/sql/*.sql` | The tutorial's ten queries, unchanged. |
| `demo/queries.py` | The ORM version of each question next to a function that runs the `.sql` file through `connection.cursor()`. |
| `demo/views.py` | `GET /reports/<name>?impl=orm|sql` returns the rows, the time and the SQL captured with `CaptureQueriesContext`. |
| `demo/management/commands/compare_impls.py` | Runs every question both ways and fails if the rows differ. |

How the ORM writes each query:

| Question | ORM | Notes |
|----------|-----|-------|
| `staff-rentals` | `values("staff_id").annotate(..., rentals=Count("*"))` | `values()` before `annotate()` is the `GROUP BY`. Django reads `store_id` from `staff`, so it skips the join to `store`. |
| `frequent-customers` | `annotate(rentals=Count("rental")).filter(rentals__gt=40)` | A filter on an aggregate becomes `HAVING`. Django follows a reverse relation with `LEFT OUTER JOIN` and counts `rental_id`; with `> 40` the result is the same as the inner join. |
| `rentals-per-customer` | `annotate(rentals=Count("rental"), joined_rows=Count("*"))` | The reverse relation is a `LEFT OUTER JOIN`. `Count("rental")` becomes `COUNT(rental.rental_id)`, so the two customers with no rentals get 0 next to a `COUNT(*)` of 1, as in the SQL. |
| `films-without-inventory` | `filter(~Exists(Inventory.objects.filter(film_id=OuterRef("film_id"))))` | Reads well and produces `NOT EXISTS`. |
| `customers-without-rentals` | `filter(rental__isnull=True)` | Produces exactly the tutorial's `LEFT OUTER JOIN ... WHERE rental.rental_id IS NULL`. |
| `duplicate-customer-names` | `filter(Exists(...))` + pairs built in Python | No self join in the ORM: Django joins a model to itself only along a foreign key, and `customer` has none to `customer`. One query finds the customers that have a namesake (a correlated `EXISTS`); Python builds the pairs. |
| `films-longer-than-average` | `aggregate(Avg("length"))`, then `filter(length__gt=Value(avg))` | Two queries, like `above-average-spenders`. Without `Value()` Django casts 115.27 to the column type and sends `115`. |
| `films-above-rating-average` | `filter(length__gt=Subquery(...filter(rating=OuterRef("rating"))...))` | `Subquery` with `OuterRef` is a correlated subquery, as in the SQL. `rating` is a PostgreSQL enum, mapped as a `TextField`. |
| `customer-totals` | `annotate(rentals=Coalesce(Subquery(...)), paid=Coalesce(Subquery(...)))` | The naive `annotate(Count("rental"), Sum("payment__amount"))` joins both tables at once and multiplies the rows. Two correlated subqueries in `SELECT` give the right totals; Django cannot put a subquery in `FROM`. |
| `above-average-spenders` | two queries | The awkward one. Django has no `WITH`, so the average is computed by one query (`aggregate()` over an annotated queryset, which Django wraps in a subquery) and passed as a literal into the second. The SQL version does it in one statement and is easier to read. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s05_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py compare_impls
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`. The migration only records the unmanaged models; it creates no tables.

```bash
curl 'localhost:8001/reports/staff-rentals?impl=orm'
curl 'localhost:8001/reports/staff-rentals?impl=sql'
curl 'localhost:8001/reports/frequent-customers?impl=orm'
curl 'localhost:8001/reports/rentals-per-customer?impl=orm'
curl 'localhost:8001/reports/films-without-inventory?impl=sql'
curl 'localhost:8001/reports/customers-without-rentals?impl=orm'
curl 'localhost:8001/reports/duplicate-customer-names?impl=orm'
curl 'localhost:8001/reports/films-longer-than-average?impl=orm'
curl 'localhost:8001/reports/films-above-rating-average?impl=orm'
curl 'localhost:8001/reports/customer-totals?impl=orm'
curl 'localhost:8001/reports/above-average-spenders?impl=orm'
```

On a fresh copy of Pagila: 2 staff rows, 669 customers with more than 40 rentals, 999 customers with their rental count, 42 films without inventory, 2 customers without rentals, 20 pairs of customers with the same name, 489 films longer than the average, 497 films longer than their rating's average, 999 customer totals and 592 customers above the average spend.

## Things to try

- Compare the `sql` field of `?impl=orm` and `?impl=sql` for each question. Which joins did Django add or leave out?
- In `frequent_customers_orm()`, add a second aggregate, `payments=Count("payment")`, next to `rentals`. Customer 380 goes from 97 rentals to 9,312: joining two 1:N relations multiplies the rows. `Count(..., distinct=True)` on both brings it back to 97.
- In `customer_totals_orm()`, replace both subqueries with `annotate(rentals=Count("rental"), paid=Sum("payment__amount"))` and run `compare_impls`. Customer 1 goes from 66 rentals and 217.35 paid to 4,290 and 14,345.10. Look at the SQL: two `LEFT OUTER JOIN`s from `customer`.
- In `customers_without_rentals_orm()`, change `rental__isnull=True` to `False`. Django switches to an `INNER JOIN` and returns 51,805 rows, one per rental, with each customer repeated. Add `.distinct()` to get 997.
- In `films_longer_than_average_orm()`, remove the `Value()` and look at the second statement in the `sql` field.
- Change `> 40` to `> 0` in both versions. Does the `LEFT OUTER JOIN` still give the same rows as the inner join? What about `>= 0`?
- Print the ORM query without running it: `print(Customer.objects.annotate(...).query)` in `uv run python manage.py shell`.
- Try to write the CTE question as one ORM query with `Subquery`. Compare the result with the two-query version and with the SQL file.
