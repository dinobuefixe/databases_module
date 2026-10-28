# Session 12 in FastAPI: Alembic migrations and a transactional API

Puts Pagila's existing `customer` table under Alembic, adds `balance` and the three-step `tier` column with migrations that can be reversed, and exposes a charge endpoint that locks the row and returns 409 when the balance is too low.

| File | What it shows |
|------|---------------|
| `alembic.ini` | Alembic settings. No database URL: it comes from `.env`. |
| `migrations/env.py` | `target_metadata = Base.metadata`, `DATABASE_URL` from the environment, and an `include_object` filter so autogenerate does not propose dropping the Pagila tables and columns we do not map. |
| `migrations/versions/0001_baseline.py` | The baseline: an empty revision that marks "Pagila as it already exists". |
| `migrations/versions/0002_customer_balance.py` | `balance numeric(10,2) NOT NULL DEFAULT 0` in one step, thanks to the server default. |
| `migrations/versions/0003_customer_tier.py` | `tier` in three steps: add nullable, backfill from `active`, set `NOT NULL`. `downgrade()` drops it. |
| `app/models.py` | `Customer` with the columns the API uses, including the two new ones. |
| `app/db.py` | Engine with a connection pool, `get_session` dependency (one session per request). |
| `app/main.py` | `GET /customers/{id}`, `POST /customers/{id}/top-up`, `POST /customers/{id}/charge` with `with session.begin()` and `with_for_update()`. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s12_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run alembic current          # 0003 (head)
uv run alembic check            # "No new upgrade operations detected": models and database agree
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl localhost:8000/customers/1
curl -X POST localhost:8000/customers/1/top-up  -H 'content-type: application/json' -d '{"amount": "20.00"}'
curl -X POST localhost:8000/customers/1/charge  -H 'content-type: application/json' -d '{"amount": "7.50"}'
curl -X POST localhost:8000/customers/1/charge  -H 'content-type: application/json' -d '{"amount": "100"}'   # 409
curl -X POST localhost:8000/customers/9999/charge -H 'content-type: application/json' -d '{"amount": "1"}'   # 404
curl -X POST localhost:8000/customers/1/charge  -H 'content-type: application/json' -d '{"amount": "-1"}'    # 422
```

## Migrating an existing database

Pagila existed before Alembic. The tutorial's `uv run alembic revision --autogenerate -m "initial schema"` compares the models with the database; because `customer` and the mapped columns are already there, the result is an empty migration. That empty migration is `0001_baseline.py`. On a new copy of Pagila, `alembic upgrade head` runs it (a no-op) and then the real changes. If a database already has every change applied by hand, `uv run alembic stamp head` records that without running anything.

Without the `include_object` filter in `env.py`, autogenerate sees about twenty Pagila tables and many `customer` columns and indexes that are not in `Base.metadata`, and writes `drop_table` and `drop_column` for all of them. Always read a generated migration before you apply it.

## Things to try

- Undo and redo: `uv run alembic downgrade -1` removes `tier`, `uv run alembic downgrade base` removes `balance` too, `uv run alembic upgrade head` brings both back. Check with `\d customer` in `psql` after each step.
- See the SQL without running it: `uv run alembic upgrade 0001:head --sql`.
- Run `uv run alembic downgrade 0002`, then delete `0003_customer_tier.py` and run `uv run alembic revision --autogenerate -m "tier"`. Autogenerate writes one `add_column(..., nullable=False)`; `uv run alembic upgrade head` fails with `column "tier" of relation "customer" contains null values`. That is why the three steps exist. Afterwards delete the generated file, restore `0003_customer_tier.py` (`git checkout`) and run `uv run alembic upgrade head`.
- Fire 20 charges of 1 at the same time on a balance of 12.50 and count the results; exactly 12 succeed and the balance never goes negative:

  ```bash
  seq 20 | xargs -P 20 -I{} curl -s -o /dev/null -w '%{http_code}\n' \
      -X POST localhost:8000/customers/1/charge -H 'content-type: application/json' -d '{"amount": "1"}' | sort | uniq -c
  ```

  Top up 12.00 to get back to 12.50, remove `.with_for_update()` from `charge` (uvicorn reloads) and run it again. More than 12 return 200, often all 20: several requests read the same old balance, so their updates overwrite each other (lost updates).
- In `app/db.py`, set `pool_size=1, max_overflow=0` and repeat: the requests queue for the single connection.
