# Runbook: restore one engine

Use this when PostgreSQL, MongoDB or Redis has lost its data: a deleted volume, a corrupted data directory, a server rebuilt from scratch. Follow it top to bottom. If you need to do anything it does not say, add it here afterwards.

## What lives where

| Data | Engine | Kind | How it comes back |
|------|--------|------|-------------------|
| `account`, `rental`, `customer`, `payment` | PostgreSQL | source of truth | `scripts/restore.sh postgres` from the newest dump |
| `monthly_reports` | MongoDB | frozen copy, cannot be regenerated with the same `generated_at` | `scripts/restore.sh mongo` from the newest archive |
| `customer:{id}:films` | Redis | derived from `rental` | `scripts/restore.sh redis` rebuilds it from PostgreSQL |

## Prerequisites

- The repository cloned, `.env` at the root and `.env` in this folder (copied from `.env.example`).
- [uv](https://docs.astral.sh/uv/) installed. The scripts run Python through `uv run`, which creates `.venv/` from `uv.lock` the first time.
- Files in `backups/`: `postgres_*.dump`, `roles_*.sql`, `mongo_*.archive.gz` and `counts_*.txt` from `scripts/backup.sh`. The newest of each is used.
- Restore PostgreSQL before Redis: the Redis rebuild reads PostgreSQL.

## Steps

1. Start the engine that was lost and wait until it is healthy:

   ```bash
   docker compose up -d <postgres|mongo|redis>     # from the repository root
   docker compose ps                               # STATUS shows (healthy)
   ```

2. Only for PostgreSQL on a new volume: create the roles first, because `pg_dump` does not include them.

   ```bash
   docker compose exec -T postgres psql -U postgres -d postgres < sessions/17-integration-disaster-day/django/backups/roles_<timestamp>.sql
   ```

   Errors saying a role already exists (`postgres`) are expected.

3. Restore, from this folder, and record the time:

   ```bash
   time scripts/restore.sh postgres     # about 1 s with this data
   time scripts/restore.sh mongo        # under 1 s
   time scripts/restore.sh redis        # about 2 s
   ```

   After a PostgreSQL restore, also run `scripts/restore.sh redis`: Redis may hold films from rentals that the backup does not have.

4. Verify:

   ```bash
   scripts/verify.sh
   ```

   It compares row counts, document counts and one known query (customer 1's payments) with the counts saved at backup time, then runs the Redis verification. Exit code 0 means everything matches. A `-` line in the diff is data written after the backup: write down how much, it is the RPO.

5. Start the API (`uv run python manage.py runserver 8001`), check `curl localhost:8001/health`, and run `uv run pytest tests/concurrency -v`.

6. Tell the rest of the group in the project channel: which engine, when it failed, RTO (step 1 to the end of step 4) and RPO (what the diff showed).

## Rehearsal

In your own group project, rehearse with the real failure:

```bash
scripts/backup.sh
docker compose stop mongo
docker compose rm -f mongo
docker volume rm <project>_mongo_data
docker compose up -d mongo
time scripts/restore.sh mongo
scripts/verify.sh
```

In the course repository the engines are shared with other projects, so do not remove volumes there. `scripts/simulate-disaster.sh <engine>` loses only this project's data (`DROP DATABASE s17_django`, `dropDatabase` on the Mongo database, `FLUSHDB` on Redis database 2), and `scripts/restore-clean-container.sh` restores the newest backups into new, empty `postgres:18` and `mongo:8` containers and removes them afterwards.

## Log of rehearsals

| Date | Engine | RTO | RPO | What was missing from this runbook |
|------|--------|-----|-----|------------------------------------|
| 2026-10-07 | postgres | 1 s restore + 2 s Redis rebuild | 1 rental written after the backup | Redis held the film from that rental; added "after a PostgreSQL restore, also run `restore.sh redis`" to step 3 |
| 2026-10-07 | mongo | under 1 s | none | nothing |
| 2026-10-07 | redis | 2 s | none (derived data) | nothing |
