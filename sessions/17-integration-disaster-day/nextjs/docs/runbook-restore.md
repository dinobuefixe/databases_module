# Runbook: restore after losing one engine

Example runbook for the session 17 project. Follow it from top to bottom; do not skip a step because "it is probably fine". Every time you have to do something this file does not say, add it here.

## What lives where

| Data | Engine | Kind | How it comes back |
|------|--------|------|-------------------|
| `account`, `customer`, `inventory`, `rental`, `payment` | PostgreSQL | source of truth | `scripts/restore.sh postgres` from the last backup |
| `monthly_reports` | MongoDB | frozen reports, cannot be regenerated identically | `scripts/restore.sh mongo` from the last backup |
| `customer:{id}:films` | Redis | derived from PostgreSQL | `scripts/restore.sh redis` rebuilds it; never backed up |

Backups: `npm run backup` writes `backups/<timestamp>/` with `postgres.dump`, `mongo.archive.gz` and `counts.txt`, and points `backups/latest` at it. In a real deployment, copy the folder off the machine.

## 0. Before you start

1. Write down the time. The time to restore (RTO) is measured from now.
2. `docker compose ps`: which engine is missing or unhealthy?
3. Stop the API (`Ctrl+C` on `npm run dev`). Requests during the restore would write to a half-restored database.
4. Check the backup exists: `ls -l backups/latest/`. Write down its timestamp: anything written after it is lost (RPO).

## 1. Bring the engine back, empty

On your own machine, after the volume was deleted:

```bash
docker compose up -d <engine>
docker compose ps          # wait for "healthy"
```

## 2. Restore

PostgreSQL:

```bash
time ./scripts/restore.sh postgres
time ./scripts/restore.sh redis      # the Redis sets were built from the old PostgreSQL data
```

MongoDB:

```bash
time ./scripts/restore.sh mongo
```

Redis:

```bash
time ./scripts/restore.sh redis
```

## 3. Verify

```bash
./scripts/verify.sh
echo $?        # must be 0
```

It checks:

1. Row and document counts against `backups/latest/counts.txt`. A count lower than the backup means data was lost; higher means writes happened after the backup.
2. Known queries: the `account_balance_check` constraint exists, Prisma's migration history has 2 entries, the frozen report `2022-07` is in MongoDB.
3. Every Redis set against PostgreSQL (`scripts/redis-verify.ts`).

Then start the API and run the concurrency tests against it:

```bash
npm run dev
npm run test:concurrency
```

## 4. Record

| Engine | Started | API back | RTO | Backup timestamp | Data lost (RPO) | Steps not in this runbook |
|--------|---------|----------|-----|------------------|-----------------|---------------------------|
| | | | | | | |

## Known problems

- `restore.sh postgres` prints `NOTICE: database "s17_nextjs" does not exist, skipping` after a real volume loss. That is expected.
- If `restore.sh mongo` says `No backups/latest/mongo.archive.gz`, nobody ran `npm run backup` after the report collection was created. The frozen reports are then lost: they cannot be regenerated with the same `generated_at`.
