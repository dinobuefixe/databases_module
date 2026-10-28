# Session 04 in Next.js with Prisma: CRUD, upsert and bulk data

The tutorial's queries on a copy of Pagila: filtered reads, an insert that returns the generated key, an update checked against an expected row count, an upsert, and three ways to load 100,000 rows with their timings.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | `npx prisma db pull` output trimmed to `film` and `actor`, plus the new `film_views` and `person` tables. |
| `prisma/migrations/0_init/migration.sql` | Baseline: the existing tables, marked as applied and never run. |
| `prisma/migrations/1_film_views_person/migration.sql` | The new tables, applied with `prisma migrate deploy`. |
| `src/app/api/films/route.ts` | `GET /api/films` with rating, title search (`ILIKE`), sort, `limit` and `offset`. |
| `src/app/api/actors/route.ts` | `POST /api/actors`: `INSERT ... RETURNING` gives back `actor_id` and `last_update`. |
| `src/app/api/films/rental-rate/route.ts` | Safe `UPDATE` in a transaction: rolled back when the row count is not the expected one. |
| `src/app/api/films/[id]/views/route.ts` | Upsert into `film_views` (`INSERT ... ON CONFLICT DO UPDATE`). |
| `scripts/bulk-person.ts` | The same Faker rows (seed 42) loaded with `COPY`, one `INSERT` per row, and `createMany`. |
| `scripts/bulk-reading.ts` | `generate_series` with `setseed(0.42)`: one million reproducible rows in SQL. |

## Prisma on an existing database

Pagila already exists, so we did not write its tables in Prisma first. The steps were:

1. `npx prisma db pull` writes a model for every table. We kept the two this session uses; Prisma ignores the rest.
2. `npx prisma migrate diff --from-empty --to-schema prisma/schema.prisma --script -o prisma/migrations/0_init/migration.sql` writes the baseline. `npx prisma migrate resolve --applied 0_init` records it as applied without running it.
3. The new models were added to `schema.prisma`, and their migration was written with `npx prisma migrate diff --from-schema <previous schema.prisma> --to-schema prisma/schema.prisma --script`.
4. `npx prisma migrate deploy` applies it.

Why not `prisma migrate dev`? It compares the database with the migration history and finds the other Pagila tables, which no migration creates. It calls that drift and offers to reset the schema, which would delete all of Pagila. `migrate deploy` only applies pending migrations and never resets.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s04_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run db:baseline      # prisma migrate resolve --applied 0_init
npm run db:deploy        # prisma migrate deploy
npm run dev
```

```bash
curl 'localhost:3000/api/films?rating=R&q=love&sort=length&order=desc&limit=10'
curl 'localhost:3000/api/films?rating=PG-13&sort=title&limit=5&offset=5'
curl -X POST localhost:3000/api/actors -H 'content-type: application/json' \
  -d '{"first_name": "ADA", "last_name": "LOVELACE"}'
curl -X POST localhost:3000/api/films/1/views     # views: 1
curl -X POST localhost:3000/api/films/1/views     # views: 2
```

The safe update. On a fresh copy of Pagila, 73 `NC-17` films have a rental rate below 1:

```bash
# wrong expectation: 409, nothing changed
curl -X POST localhost:3000/api/films/rental-rate -H 'content-type: application/json' \
  -d '{"rating": "NC-17", "below": 1, "newRate": 1.99, "expectedCount": 5}'
# right expectation: committed, the 73 rows come back (UPDATE ... RETURNING)
curl -X POST localhost:3000/api/films/rental-rate -H 'content-type: application/json' \
  -d '{"rating": "NC-17", "below": 1, "newRate": 1.99, "expectedCount": 73}'
```

Bulk loads:

```bash
npm run bulk:person              # 100,000 rows each way
npm run bulk:person -- 20000     # fewer rows
npm run bulk:reading             # 1,000,000 rows with generate_series
```

Typical output of `bulk:person` on a laptop:

```
COPY                        0.52 s   100000 rows   190941 rows/s
INSERT per row             23.84 s   100000 rows   4194 rows/s
Prisma createMany           4.97 s   100000 rows   20113 rows/s
```

`createMany` sends multi-row `INSERT` statements, which is why it sits between the other two. With large loads you may see a `DeprecationWarning` from `pg` during `createMany`; it comes from inside Prisma's adapter and does not affect the result.

## Things to try

- Set `LOG_QUERIES=1` in `.env`, restart, and call the endpoints. The upsert is one `INSERT ... ON CONFLICT ("film_id") DO UPDATE`; the title search is `ILIKE ('%' || $1 || '%')`; the safe update is one `UPDATE ... RETURNING`.
- Ratings come back as `PG_13` and `NC_17`. Prisma enum values must be valid identifiers, so the schema maps them with `@map("PG-13")`. Compare with `SELECT DISTINCT rating FROM film;` in `psql`.
- Run `npm run bulk:reading` twice: `sum(value)` is the same both times because of `setseed`. Remove the transaction in `scripts/bulk-reading.ts` and run it again: `setseed` may then run on a different pooled connection from the `CREATE TABLE`, and the sum is no longer guaranteed to repeat.
- Run the upsert for film 99999: the foreign key to `film` refuses it, and the API answers 404.
- Change `escape()` in `scripts/bulk-person.ts` to return the value unchanged and add a name with a tab in it. `COPY` reads it as an extra column and fails.
