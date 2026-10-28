# Session 17 in Next.js with Prisma: integration and disaster day

A small API that uses all three engines together, with concurrency tests that run against the live API and the backup, restore and verify scripts from the session 17 tutorial, rehearsed engine by engine.

| File | What it shows |
|------|---------------|
| `prisma/migrations/0_init/` | Baseline of the Pagila tables the API maps, marked as applied. |
| `prisma/migrations/1_account/` | The `account` table from session 08 with its `CHECK (balance >= 0)`, added by hand to the generated SQL, and two accounts of 100. |
| `src/app/api/accounts/[id]/withdraw/route.ts` | Atomic conditional `UPDATE` with `updateMany` and `count` (session 08). |
| `src/app/api/rentals/route.ts` | Writes the rental to PostgreSQL, then adds the film to `customer:{id}:films` in Redis (session 16). |
| `src/app/api/reports/monthly/[month]/route.ts` | Frozen monthly report from PostgreSQL into MongoDB, 201 then 409 (session 14). |
| `src/app/api/verify/route.ts`, `src/lib/films-sets.ts` | Rebuild and verification of the Redis sets. |
| `tests/concurrency/` | `node:test` tests that fire concurrent requests at the running API and assert each rule. |
| `scripts/backup.sh` | `pg_dump -Fc` and `mongodump` into `backups/<timestamp>/`, plus the counts at that moment. |
| `scripts/restore.sh <postgres\|mongo\|redis>` | Restores one engine. Redis is restored by rebuilding it from PostgreSQL. |
| `scripts/verify.sh` | Counts against the backup, known queries, Redis verification. Exit code 0 or 1. |
| `scripts/disaster.sh <engine>` | Simulates the loss of one engine, limited to this project's databases. |
| `scripts/clean-volume-check.sh` | Restores the backup into brand-new `postgres:18` and `mongo:8` containers and compares the counts. |
| `docs/runbook-restore.md` | The runbook the scripts belong to. |

The tutorial runs `pytest tests/concurrency`. In this project the tests use Node's built-in test runner: `npm run test:concurrency`.

### Why the migrations are applied with `migrate deploy`

The schema only maps four tables, so `prisma migrate dev` would see the rest of Pagila as drift and offer to reset the database (session 12 explains this and baselines the whole schema instead). Here `0_init` was generated from the trimmed schema with `prisma migrate diff --from-empty`, marked as applied, and `1_account` was generated with `prisma migrate diff --from-schema <schema without account> --to-schema prisma/schema.prisma --script` and edited. `prisma migrate deploy` applies pending migrations without comparing the database with the schema.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s17_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npx prisma migrate resolve --applied 0_init
npm run db:deploy
npm run redis:rebuild
npm run dev
```

In a second terminal:

```bash
npm run test:concurrency        # 3 tests, all pass
curl localhost:3000/api/health
curl -X POST localhost:3000/api/accounts/2/withdraw -H 'content-type: application/json' -d '{"amount": 30}'
curl -X POST localhost:3000/api/rentals -H 'content-type: application/json' -d '{"customer_id": 2, "inventory_id": 10}'
curl localhost:3000/api/customers/2/films
curl -X POST localhost:3000/api/reports/monthly/2022-08
curl localhost:3000/api/verify
```

## Rehearse the disaster

The tutorial deletes an engine's Docker volume:

```bash
./scripts/backup.sh
docker compose stop mongo
docker compose rm -f mongo
docker volume rm <project>_mongo_data
docker compose up -d mongo
time ./scripts/restore.sh mongo
```

Do that in your group project, where the engines are yours. The course's engines are shared by every session project, so deleting a volume would wipe everyone's data. Here `scripts/disaster.sh` deletes only this project's data instead: it drops the `s17_nextjs` PostgreSQL database, drops the `s17_nextjs` MongoDB database, or runs `FLUSHDB` on Redis database 3. The scripts refuse to run if `.env` points anywhere else.

```bash
npm run backup
npm run disaster postgres
time ./scripts/restore.sh postgres
./scripts/restore.sh redis
./scripts/verify.sh

npm run disaster mongo
./scripts/verify.sh               # FAIL: the reports are missing
time ./scripts/restore.sh mongo
./scripts/verify.sh

npm run disaster redis
time ./scripts/restore.sh redis
./scripts/verify.sh

npm run clean-volume-check        # the backup restores into empty engines
```

`clean-volume-check` is the closest equivalent of a fresh volume here: two throwaway containers (`s17-nextjs-pg-check`, `s17-nextjs-mongo-check`) with nothing in them but what the backup brings. They are removed when it finishes.

## Things to try

- Make a withdrawal and a rental after `npm run backup`, then lose and restore PostgreSQL. `verify.sh` passes, but your withdrawal and rental are gone: that is the RPO. Fill in the table at the end of the runbook.
- Restore PostgreSQL and skip `restore.sh redis`. Which check fails, and why?
- Delete one customer's set in `redis-cli` (`DEL customer:2:films`) and run `npm run test:concurrency`. The rentals test refuses to start until you rebuild.
- Hand the runbook to someone who has not seen this project and time them.
