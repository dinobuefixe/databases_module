# Session 07 in Next.js with Prisma: indexes and optimisation

The tutorial's `big_rental` table (2,000,000 rows), `EXPLAIN (ANALYZE, BUFFERS)` for its queries before and after each index, and the cost of the indexes on writes.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | The composite index (`rented_at(sort: Desc)`), the partial index (`where:`) and a plain index on `rented_at`, declared with `@@index`. |
| `scripts/create-big-rental.ts` | `npm run big-rental`: creates `big_rental` with `setseed(0.1)`, then runs `VACUUM ANALYZE` outside the transaction (`VACUUM` cannot run inside one). Row count configurable. |
| `scripts/indexes.ts` | `npm run index`: create, drop or list the tutorial indexes. |
| `src/lib/explain.ts` | The tutorial queries as `Prisma.sql` fragments, wrapped in `EXPLAIN (ANALYZE, BUFFERS)`. |
| `scripts/explain.ts` | `npm run explain`: prints the plan, the scans used and the execution time. Extra `key=value` arguments are passed as query parameters, for example `days=7` or `force_index=1`. |
| `src/app/api/explain/[query]/route.ts` | The same as JSON: `GET /api/explain/customer-latest` and the others. |
| `src/app/api/indexes/route.ts` | `GET /api/indexes`: the indexes that exist now and their size. |
| `scripts/write-cost.ts` | `npm run write-cost`: times inserting 100,000 rows with no index, one, and two. |

## Indexes in Prisma

| Tutorial index | Prisma schema | Notes |
|----------------|---------------|-------|
| `(customer_id, rented_at DESC)` | `@@index([customer_id, rented_at(sort: Desc)])` | Supported. |
| `(rented_at) WHERE returned_at IS NULL` | `@@index([rented_at], where: { returned_at: null })` | Needs `previewFeatures = ["partialIndexes"]` in the generator. Preview features can change between Prisma versions. |
| `customer (lower(email))` | not possible | `@@index` only takes columns. Raw SQL in `scripts/indexes.ts`; in a real project, a migration edited by hand. |
| `(rented_at)` | `@@index([rented_at])` | Supported. Here to show an index the planner ignores. |

Print the SQL Prisma generates from the schema with:

```bash
npx prisma migrate diff --from-empty --to-schema prisma/schema.prisma --script
```

The three `CREATE INDEX` statements match the tutorial's, and `scripts/indexes.ts` runs those same statements. In a project you would let a migration create the indexes once. Here the scripts create and drop them on demand, because the point is to measure each query with and without them. The table itself is created with `CREATE TABLE ... AS SELECT ... generate_series`, which Prisma cannot express.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s07_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run big-rental                 # 2,000,000 rows; npm run big-rental -- 500000 for fewer
npm run explain                    # before: Seq Scan
npm run index -- create composite
npm run explain -- customer-latest # after: Index Scan using big_rental_customer_rented
npm run index -- create partial
npm run index -- create lower-email
npm run explain
npm run index -- create single
npm run explain -- recent-rentals                 # Seq Scan: the index is ignored
npm run explain -- recent-rentals force_index=1   # Index Scan, forced
npm run explain -- recent-rentals days=7          # Bitmap Index Scan on big_rental_rented
npm run write-cost
npm run index -- drop all
npm run dev
```

```bash
curl 'localhost:3000/api/explain/customer-latest?customer=42'
curl localhost:3000/api/explain/open-rentals
curl 'localhost:3000/api/explain/customer-email?email=MARY.SMITH@sakilacustomer.org'
curl 'localhost:3000/api/explain/recent-rentals?days=730&force_index=1'
curl localhost:3000/api/indexes
```

Results on a laptop (your times will differ; compare the shape of the plan and the `Buffers` line):

| Query | Before | After |
|-------|--------|-------|
| `customer-latest` | Parallel Seq Scan, ~25 ms, ~12,800 buffers | Index Scan on the composite index, ~0.1 ms, 13 buffers |
| `open-rentals` | Parallel Seq Scan, ~25-38 ms | Index Only Scan using `big_rental_open`, ~5-12 ms |
| `customer-email` | Seq Scan on 999 rows, ~0.5 ms | Bitmap Index Scan on `customer_lower_email`, ~0.05 ms |
| `recent-rentals` (730 days) | Seq Scan, ~180 ms, 12,736 buffers | still Seq Scan; forced Index Scan ~470 ms, ~1,337,000 buffers |
| `recent-rentals` (`days=7`) | Parallel Seq Scan, ~60 ms | Bitmap Index Scan on `big_rental_rented`, ~6 ms |

`recent-rentals` is the index the planner does not use. With 730 days, 1,334,083 of the 2,000,000 rows match, so it reads the whole table, each page once. `force_index=1` turns off sequential and bitmap scans for that one query, inside a transaction with `SET LOCAL`, to show the plan it rejected: the index is in date order, the rows are stored in no particular order, so almost every row means a jump to another page. With `days=7` only 13,000 rows match and the same index wins.

`write-cost` output:

```
no indexes                        33 ms
composite                         63 ms
composite + partial               94 ms
```

Each insert runs in a transaction that is rolled back, so the table stays at its original size, and the script restores the indexes that existed when it started.

## Things to try

- The partial index is small (about 1.3 MB against 60 MB for the composite one), and `open-rentals` reads it with an `Index Only Scan`: compare the `Buffers` line before and after. Why is the partial index so much smaller, and why can the query be answered from the index alone? Write it down in one sentence, as the tutorial asks.
- Run `customer-email` with `WHERE email = ...` instead of `lower(email) = lower(...)` (edit `src/lib/explain.ts`). The expression index is not used: the query must use the same expression as the index.
- Ask for a filter on `rented_at` alone, without `customer_id`. Can the composite index help? Check with `EXPLAIN` in `psql`.
- Run `npm run big-rental -- 20000` and repeat `npm run explain`: on a small table the planner may prefer a sequential scan even with the index in place.
- Prisma's `findMany({ where: { customer_id: 42 }, orderBy: { rented_at: "desc" }, take: 10 })` sends the same query as `customer-latest`. Indexes help ORM queries exactly as they help hand-written SQL.
- `docker-compose.yml` preloads `pg_stat_statements`. Run `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` in `psql` on this database, call the endpoints a few times, then `SELECT query, calls, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 5;`.
