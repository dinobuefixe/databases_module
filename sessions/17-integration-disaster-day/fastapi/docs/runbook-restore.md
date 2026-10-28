# Runbook: restore one engine

For the session 17 example API (`s17_fastapi`). Follow it top to bottom; every command runs from this project's folder (`sessions/17-integration-disaster-day/fastapi`) unless it says "repository root".

## When to use it

- One engine's data is gone or damaged: the Docker volume was removed, the database was dropped, Redis was flushed.
- `./scripts/verify.sh` fails and the cause is missing data, not a bug in the code.

If two engines are gone, restore PostgreSQL first, then MongoDB, then Redis: Redis is rebuilt from PostgreSQL.

## What each engine holds

| Engine | Data | Group | How it comes back |
|--------|------|-------|-------------------|
| PostgreSQL `s17_fastapi` | Pagila, `account` | Source of truth | `pg_restore` from the newest `backups/*/postgres.dump` |
| MongoDB `s17_fastapi` | `monthly_reports` | Source of truth for reports already sent (frozen: generating them again could give different numbers) | `mongorestore` from the newest `backups/*/mongo.archive.gz` |
| Redis database `/1` | `customer:{id}:films` sets | Derived from rentals | Rebuilt from PostgreSQL, no backup file |

## Prerequisites

- Docker running, and `docker compose ps` (repository root) shows the engine `healthy`.
- `.env` in this folder (copy of `.env.example`) and `uv sync` run once in this folder. The scripts call Python through `uv run`, so no virtual environment needs to be activated.
- At least one folder in `backups/`. Check with `ls -t backups | head -1`. If there is none, there is nothing to restore from: stop and tell the group.

## Steps

1. Stop sending traffic to the API (stop `uvicorn`), so nothing writes while you restore.
2. If the engine's container is gone, start it (repository root): `docker compose up -d <postgres|mongo|redis>` and wait for `healthy` in `docker compose ps`.
3. Restore, and note the time printed at the end:

   ```bash
   time ./scripts/restore.sh postgres     # or mongo, or redis
   ```

   To use an older backup: `./scripts/restore.sh postgres backups/<timestamp>`.
4. If PostgreSQL was restored, rebuild Redis too, because rentals made after the backup are gone from PostgreSQL but may still be in Redis:

   ```bash
   ./scripts/restore.sh redis
   ```

5. Verify, before the API takes new writes:

   ```bash
   ./scripts/verify.sh; echo $?
   ```

   It compares row counts (`customer`, `film`, `inventory`, `rental`, `payment`, `account`), document counts and one known query (`SELECT count(*) FROM rental WHERE customer_id = 1`) with the snapshot taken at backup time, then runs the Redis verification. Expected: every line `ok`, `redis: OK`, `VERIFY PASSED`, exit code 0.
6. Start the API (`uv run uvicorn app.main:app --port 8000`) and check that `curl localhost:8000/health` returns `ok` for the three engines.
7. Write down the RTO (the time from step 3, plus the time to notice) and the RPO (the age of the backup: everything written after it is lost). Tell the group in the project channel.

## Expected times (measured on the course laptop setup)

| Engine | Restore time | Backup size |
|--------|--------------|-------------|
| PostgreSQL | about 1 s | 4.4 MB |
| MongoDB | under 1 s | under 1 KB (a few reports) |
| Redis | about 1.5 s (0.06 s for the rebuild itself) | none |

## If something fails

- `pg_restore: error: could not execute query: ERROR: role "..." does not exist`: the dump has owners or grants for roles that are gone with the volume. Restore the roles first from `pg_dumpall --roles-only` (session 10), or rely on `--no-owner`, which `restore.sh` already passes.
- `verify.sh` shows `DIFF` with a higher `now` value: something wrote after the restore. Run it straight after step 3 or 4.
- `verify.sh` shows `DIFF` with a lower `now` value after a restore: those rows were written after the backup. That is the real RPO; record it.
- The API returns 500 right after a PostgreSQL restore: its pooled connections pointed at the dropped database. `pool_pre_ping=True` in `app/db.py` replaces them on the next request; if not, restart `uvicorn`.

## Rehearsal

On your own machine, the real rehearsal deletes the engine's volume (repository root):

```bash
sessions/17-integration-disaster-day/fastapi/scripts/backup.sh
docker compose stop mongo
docker compose rm -f mongo
docker volume rm databases-module_mongo_data
docker compose up -d mongo
cd sessions/17-integration-disaster-day/fastapi && time ./scripts/restore.sh mongo && ./scripts/verify.sh
```

The volume name is `<compose project name>_<volume>`; list them with `docker volume ls`. For PostgreSQL, a lost volume also loses the `pagila` template and every other project's database; `restore.sh postgres` only brings back `s17_fastapi`.

On a machine shared with other people, never remove a volume. Use `./scripts/simulate-loss.sh <engine>` instead, which drops only this project's PostgreSQL database, this project's Mongo database, or this project's Redis logical database (`FLUSHDB`), and refuses to run if `.env` points at a database whose name does not start with `s17_`.
