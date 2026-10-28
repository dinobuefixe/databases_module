# Session 11 in Django: the N+1 problem and eager loading

The session 11 tutorial with the Django ORM instead of SQLAlchemy: `customer` and `rental` mapped as models, the N+1 problem when listing 20 customers with their rental counts, the fix with eager loading, and the top 5 customers by rentals aggregated in the database. Every endpoint reports how many SQL statements it ran.

| File | What it shows |
|------|---------------|
| `demo/models.py` | `Customer` and `Rental` mapped to the existing Pagila tables with `managed = False`. The `ForeignKey` with `related_name="rentals"` gives `customer.rentals`. |
| `demo/views.py` | `GET /customers?eager=false\|true` (1:N, `prefetch_related`), `GET /rentals?eager=false\|true\|peers` (N:1, `select_related` and a fetch mode), `GET /customers/top` (`annotate(Count(...))`). Queries are counted with `CaptureQueriesContext`. |
| `demo/management/commands/n_plus_one.py` | The tutorial script as a management command: the three blocks with their query counts. |
| `config/settings.py` | `LOGGING` for the `django.db.backends` logger, the Django version of `echo=True`. |
| `demo/migrations/0001_initial.py` | Records the unmanaged models. It creates no tables. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s11_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py n_plus_one
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl 'localhost:8001/customers?limit=20&eager=false'   # "queries": 21
curl 'localhost:8001/customers?limit=20&eager=true'    # "queries": 2
curl 'localhost:8001/rentals?limit=20&eager=false'     # "queries": 21
curl 'localhost:8001/rentals?limit=20&eager=true'      # "queries": 1, a JOIN
curl 'localhost:8001/rentals?limit=20&eager=peers'     # "queries": 2
curl 'localhost:8001/customers/top?limit=5'
```

With `SQL_LOG=true` in `.env`, the terminal running `runserver` prints every statement with its duration. Count them for each request.

## Django and SQLAlchemy names

| SQLAlchemy 2 | Django |
|--------------|--------|
| `Engine` and its pool | `DATABASES` in settings; one connection per thread, kept open for `CONN_MAX_AGE` seconds |
| `Session` | No equivalent object. Each `QuerySet` runs its own SQL; `transaction.atomic()` groups writes |
| `DeclarativeBase`, `__tablename__` | `models.Model`, `Meta.db_table` |
| `Mapped[int] = mapped_column(primary_key=True)` | `models.AutoField(primary_key=True)` |
| `ForeignKey(...)` plus `relationship(back_populates=...)` | One `models.ForeignKey(..., related_name=...)` |
| `select(Customer).where(...).limit(20)` | `Customer.objects.filter(...)[:20]` |
| `selectinload(Customer.rentals)` | `prefetch_related("rentals")` |
| `joinedload(Rental.customer)` | `select_related("customer")` |
| `func.count(Rental.rental_id)` with `group_by` | `annotate(n=Count("rentals"))` |
| `create_engine(..., echo=True)` | `LOGGING` on `django.db.backends`, only when `DEBUG = True` |
| `before_cursor_execute` event | `CaptureQueriesContext(connection)` or `connection.execute_wrapper()` |

## Things to try

- Raise `limit` to 100 with `eager=false` and watch the count become 101 and the response time grow.
- Compare the SQL in `/customers/top` with the tutorial's SQLAlchemy query. Django uses a `LEFT OUTER JOIN`, so a customer with no rentals would appear with `n = 0`; the tutorial's `.join()` is an inner join and would leave them out.
- Replace `len(c.rentals.all())` with `c.rentals.count()` in `views.py`. With `eager=false` there are still 21 queries, but each one is now `SELECT COUNT(*)` instead of fetching every rental row. With `eager=true`, `.count()` uses the prefetched rows. `Customer.objects.annotate(n=Count("rentals"))` gets the same numbers in one query without loading any rental rows.
- In `uv run python manage.py shell`, run `Rental.objects.fetch_mode(FETCH_RAISE)[:5]` (import it from `django.db.models`) and access `.customer` on one of them: Django raises `FieldFetchBlocked` instead of running a hidden query. This is a quick way to find lazy loads in tests.
- Call `.explain(analyze=True)` on the queryset of `/customers/top` in the shell and read the plan.
