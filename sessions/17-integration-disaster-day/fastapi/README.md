# Session 17 in FastAPI: integration and disaster day

A small API that uses the three engines together (account withdrawals in PostgreSQL, rentals that keep a derived Redis set up to date, frozen monthly reports in MongoDB), a concurrency test suite that runs against the running API, and the backup, restore and verify scripts that the restore runbook follows.

| File | What it shows |
|------|---------------|
| `app/main.py` | `GET /health`, `PUT /accounts/{id}`, `POST /accounts/{id}/withdraw` (atomic conditional `UPDATE`), `POST /rentals` (PostgreSQL first, then `SADD` in Redis), `GET /customers/{id}/films` (Redis and PostgreSQL side by side), `POST`/`GET /reports/monthly/{YYYY-MM}`. |
| `app/models.py` | `Account` with `CHECK (balance >= 0)`, and the Pagila `Inventory` and `Rental` columns used. |
| `app/films_sets.py` | Rebuild and verification of `customer:{id}:films` (session 16, one query and one pipeline). |
| `tests/concurrency/` | Three rules under parallel requests: 50 withdrawals of 10 from 100 (exactly 10 succeed), 20 rentals at once (Redis still agrees with PostgreSQL), 10 report requests for the same month (exactly one 201). |
| `scripts/init_db.py` | Creates the `account` table and fills Redis. |
| `scripts/backup.sh` | `pg_dump -Fc`, `mongodump --archive --gzip` and a snapshot of counts into `backups/<timestamp>/`. No Redis backup: its data is derived. |
| `scripts/restore.sh <postgres\|mongo\|redis>` | Restores one engine from the newest backup and prints the time. Redis is restored by rebuilding it. |
| `scripts/verify.sh` | Counts and a known query against the backup's snapshot, plus the Redis verification. Exit 1 on any difference. |
| `scripts/simulate-loss.sh <engine>` | Loses one engine's data for this project only, for rehearsals on a shared machine. |
| `docs/runbook-restore.md` | The runbook: when, prerequisites, commands, verification, expected times, rehearsal. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s17_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.init_db
uv run uvicorn app.main:app --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`; `pytest` and `httpx`, which only the tests use, are in the `dev` group, which `uv sync` installs by default.

```bash
curl localhost:8000/health
curl -X PUT localhost:8000/accounts/1 -H 'content-type: application/json' -d '{"balance": "100"}'
curl -X POST localhost:8000/accounts/1/withdraw -H 'content-type: application/json' -d '{"amount": "10"}'
curl -X POST localhost:8000/rentals -H 'content-type: application/json' -d '{"customer_id": 2, "inventory_id": 1}'
curl localhost:8000/customers/2/films           # {"redis": 70, "postgres": 70}
curl -X POST localhost:8000/reports/monthly/2022-07
```

With the API running, in a second terminal:

```bash
uv run pytest tests/concurrency -v
```

## Disaster rehearsal

Take a backup, lose one engine, restore it, verify:

```bash
./scripts/backup.sh
./scripts/simulate-loss.sh mongo
./scripts/verify.sh                 # DIFF mongo.monthly_reports, VERIFY FAILED
time ./scripts/restore.sh mongo
./scripts/verify.sh                 # VERIFY PASSED
```

Repeat with `postgres` and `redis`. After a PostgreSQL restore, run `./scripts/restore.sh redis` as well, as the runbook says.

`simulate-loss.sh` exists because the Docker engines in this repository are shared by many projects. The tutorial's rehearsal removes the volume (`docker compose rm -f mongo` and `docker volume rm <project>_mongo_data`), which deletes every project's data in that engine. Do that only on your own machine, for your own group project; the steps are in `docs/runbook-restore.md`.

## Things to try

- After a backup, rent a film the customer has not rented before (`{"customer_id": 3, "inventory_id": 2}`), then lose and restore PostgreSQL. In `verify.sh` the PostgreSQL counts match the snapshot, because the backup did not have the rental either, but the rental is gone: that is the RPO. The Redis check fails (`customer 3: redis=71 postgres=70`): Redis still holds the film from the lost rental. Run `./scripts/restore.sh redis` and `verify.sh` passes.
- Break the withdrawal: in `app/main.py`, read the balance with `session.get`, subtract in Python and assign it. Run `uv run pytest tests/concurrency -v` and read which assertion fails and why.
- Run the tests twice. The report test looks for a month without a report, so it keeps working until every month from 2022 to 2026 has one.
- Ask someone who did not write `docs/runbook-restore.md` to follow it for `postgres` while you watch without helping. Every question they ask is a line missing from the runbook.
