# Session 17 in Django: integration, concurrency tests and disaster day

A small API that uses the three engines together, with pieces from earlier sessions: the account withdrawal in PostgreSQL (session 08), rentals that keep the derived `customer:{id}:films` sets in Redis up to date (session 16), and the frozen monthly report in MongoDB (session 14). On top of it, the session 17 tutorial: concurrency tests against the running API, backup and restore scripts per engine, a verification script and a restore runbook.

| File | What it shows |
|------|---------------|
| `demo/views.py` | `POST /accounts/{id}/withdraw` (atomic conditional `UPDATE`), `POST /rentals` (PostgreSQL first, Redis in `transaction.on_commit`), `GET /customers/{id}/films`, `GET /verify`, `POST`/`GET /reports/monthly/{YYYY-MM}`, `GET /health`. |
| `demo/models.py` | `Account` with a `CheckConstraint` (`balance >= 0`), created by the migration; the Pagila tables, unmanaged. |
| `demo/derived.py`, `demo/reports.py` | Redis rebuild and verify; the frozen report. |
| `demo/management/commands/` | `reset_account`, `rebuild_redis`, `verify_redis`, `counts` (rows, documents and a known query, one per line so they can be diffed). |
| `tests/concurrency/` | 50 withdrawals of 10 from 100 (exactly 10 succeed), 30 concurrent rentals then Redis equals PostgreSQL, 10 concurrent report requests (exactly one `201`). |
| `scripts/backup.sh`, `scripts/restore.sh`, `scripts/verify.sh` | The disaster day scripts. Redis is restored by rebuilding it, because everything in it is derived. |
| `scripts/simulate-disaster.sh`, `scripts/restore-clean-container.sh` | A rehearsal that is safe in the shared course environment. |
| `docs/runbook-restore.md` | The runbook, with the times measured in a rehearsal. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s17_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate            # creates the account table
uv run python manage.py reset_account      # account 1 with a balance of 100
uv run python manage.py rebuild_redis
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`; `pytest` and `httpx`, which only the tests use, are in the `dev` group that `uv sync` also installs.

```bash
curl localhost:8001/health
curl -X POST localhost:8001/accounts/1/withdraw -H 'content-type: application/json' -d '{"amount": 10}'
curl -X POST localhost:8001/rentals -H 'content-type: application/json' -d '{"customer_id": 5, "inventory_id": 10, "staff_id": 1}'
curl localhost:8001/customers/5/films
curl -X POST localhost:8001/reports/monthly/2022-07
curl localhost:8001/verify
```

With the API running, in a second terminal:

```bash
uv run pytest tests/concurrency -v
```

## Disaster day rehearsal

```bash
scripts/backup.sh
scripts/simulate-disaster.sh postgres     # asks for confirmation; add --yes to skip
time scripts/restore.sh postgres
scripts/restore.sh redis
scripts/verify.sh; echo "exit code $?"
scripts/restore-clean-container.sh
```

The tutorial removes the engine's Docker volume. The engines in this repository are shared by every session's projects, so `simulate-disaster.sh` deletes only this project's data: `DROP DATABASE s17_django`, `dropDatabase()` on the `s17_django` Mongo database, and `FLUSHDB` on Redis database 2. In your group project, which has its own volumes, rehearse with `docker compose stop`, `docker compose rm -f` and `docker volume rm` as the runbook shows.

## Things to try

- Create a rental after `scripts/backup.sh`, then simulate a PostgreSQL disaster and restore it. `verify.sh` fails on Redis: the set still has the film from the lost rental. That is why the runbook rebuilds Redis after every PostgreSQL restore.
- Change `withdraw` to read the balance, compute the new value in Python and save it, then run `uv run pytest tests/concurrency/test_withdraw.py`. The test catches the lost update.
- Replace `transaction.on_commit(...)` in `create_rental` with a direct `derived.add_film(...)` call before the `Rental.objects.create`, and make the insert fail (an unknown `staff_id`). Redis now has a film the customer never rented, and `GET /verify` returns `503`.
- Time `scripts/restore.sh postgres` after `simulate-disaster.sh postgres` and compare it with the clean container restore. Write both numbers in the runbook's log.
