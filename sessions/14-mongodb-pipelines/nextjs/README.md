# Session 14 in Next.js with Prisma: aggregation pipelines and reports

Loads `films` and `customers` collections from Pagila, runs the pipelines from the session 14 tutorial (`$group`, `$unwind`, `$dateTrunc`, `$bucket`, `$facet`, `$lookup`, `$match` early and late, `$merge`), freezes a monthly payments report from PostgreSQL with a deterministic `_id`, and backs up and restores this project's MongoDB database.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | The Pagila tables the collections are built from, trimmed from `npx prisma db pull`. |
| `scripts/load-collections.ts` | `npm run load`: `films` with `length`, the list of `categories` and the actors embedded; `customers` with `store_id`, `rentals_total` (`_count`) and the last 10 rentals embedded (`take` inside `include`); an index on `recent_rentals.rental_date`. |
| `src/app/api/films/by-rating/route.ts` | `$group` by rating with `$sum` and `$avg`. |
| `src/app/api/actors/top/route.ts` | `$unwind` the embedded actors, `$group`, `$sort`, `$limit`. |
| `src/app/api/rentals/per-month/route.ts` | `$dateTrunc` on the embedded rental dates (the stages are in `src/lib/pipelines.ts`). |
| `src/app/api/customers/by-activity/route.ts` | `$bucket`: customers in ranges of total rentals. |
| `src/app/api/customers/summary/route.ts` | `$facet`: customers and rentals per store, and the 3 most active customers, in one document. |
| `src/app/api/rentals/latest/route.ts` | `$lookup`: the film's rating and categories for the 5 latest rentals. |
| `src/app/api/rentals/match-position/route.ts` | The same pipeline with `$match` late and early, and `totalDocsExamined` from `.explain("executionStats")`. |
| `src/app/api/reports/rentals-per-month/route.ts` | `POST` materialises rentals per month into `rentals_per_month` with `$merge`; `GET` reads it. |
| `src/app/api/reports/monthly/[month]/route.ts` | `POST` builds the frozen report with `$queryRaw` and `insertOne` (201, then 409 on the duplicate `_id`); `GET` reads it. |
| `src/lib/prisma.ts` | A second client for `READONLY_DATABASE_URL`, used by the report. |
| `scripts/mongo-backup.sh` | `npm run backup`: `mongodump --db ... --archive --gzip` into `backups/` (git-ignored). Writes to a `.part` file and renames it only when the dump succeeds. |
| `scripts/mongo-restore.sh` | `npm run restore`: `mongorestore` into `s14_nextjs_restored` with `--nsFrom/--nsTo`, timed, then compares document counts. |

Two changes from the tutorial:

- The report filters with a date range (`payment_date >= '2022-07-01' AND payment_date < '2022-08-01'`) rather than `to_char(payment_date, 'YYYY-MM') = '2022-07'`. `payment` is partitioned by month; with the range PostgreSQL reads one partition, with `to_char` it reads all of them.
- A month with no payments is refused (422) instead of being frozen as an empty report forever.

`READONLY_DATABASE_URL` is empty in `.env.example`, so the report uses `DATABASE_URL`. If you created the `readonly` role in session 09 and granted it `SELECT` on this database, put its URL there.

## Run it

From the root of the repository, start the engines and create this project's PostgreSQL database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s14_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run load      # films: 1000 documents, customers: 999 documents
npm run dev
```

```bash
curl localhost:3000/api/films/by-rating
curl localhost:3000/api/actors/top
curl localhost:3000/api/rentals/per-month
curl localhost:3000/api/customers/by-activity        # $bucket on rentals_total
curl localhost:3000/api/customers/summary            # $facet: per store and the 3 most active
curl localhost:3000/api/rentals/latest               # $lookup the film of the 5 latest rentals
curl localhost:3000/api/rentals/match-position       # docs_examined: 999 with $match late, 164 early
curl -X POST localhost:3000/api/reports/rentals-per-month   # {"months": 26, "rentals": 9622}, the same every time
curl localhost:3000/api/reports/rentals-per-month
curl -X POST localhost:3000/api/reports/monthly/2022-07   # 201
curl -X POST localhost:3000/api/reports/monthly/2022-07   # 409: already exists and is frozen
curl localhost:3000/api/reports/monthly/2022-07
```

Backup and restore. `mongodump` and `mongorestore` run inside the `mongo` container, where the server is `localhost:27017` whatever port your machine publishes, so the scripts log in with the root user from the `.env` at the root of the repository instead of `MONGO_URL`:

```bash
npm run backup    # Wrote backups/mongo_s14_nextjs_<timestamp>.archive.gz
npm run restore   # restores the newest backup into s14_nextjs_restored and compares counts
```

The tutorial restores with `--drop` over the original database. Here the restore goes into `s14_nextjs_restored`, so a bad backup cannot overwrite the data you are testing against. In your own project, restoring over the real database is the last step, after the restored copy has been checked.

Three things the new pipelines show:

- **`$lookup` sparingly.** `/api/rentals/latest` reads the film's rating and categories from `films` with `$lookup`, after `$limit`, so it looks up 5 films. If most queries need the rating next to a rental, copy it into `recent_rentals` in the loader instead: a join on every read is a sign the data is relational or should be embedded.
- **`$match` first.** In `/api/rentals/match-position` both pipelines return the same numbers. The late `$match` filters array elements after `$unwind`, so MongoDB cannot move it earlier and reads all 999 customers. The early one keeps only customers with a rental in the range, uses the index on `recent_rentals.rental_date`, and reads 164.
- **`$merge` is idempotent here.** The `_id` of each document is the month, and `whenMatched: "replace"` overwrites the document for a month that already exists. Run it twice and `rentals_per_month` has the same 26 documents. `$out` would also work, but it replaces the whole collection on every run.

## Things to try

- Change a payment amount in July 2022 in PostgreSQL and `POST` the report again. It is still refused, and `GET` still shows the old revenue: that is what frozen means.
- `/api/rentals/per-month` starts in 2024 although rentals start in 2022. Only the last 10 rentals of each customer are embedded. Compare with `SELECT date_trunc('month', rental_date), count(*) FROM rental GROUP BY 1 ORDER BY 1` in `psql`.
- Add a `$match: { rating: "PG" }` stage at the start of the films-by-rating pipeline, then `$match: { _id: "PG" }` at the end, and compare `totalDocsExamined` with `.explain("executionStats")` in `mongosh`. They are the same: MongoDB moves a `$match` on the group key before `$group` for you. It cannot do that in `/api/rentals/match-position`, because there the filter is on the elements that `$unwind` produces.
- Open `mongosh` on `s14_nextjs_restored` and run one of the pipelines there. Then delete a few films from `s14_nextjs`, run `npm run restore` with the older backup file and read the `MISMATCH` lines.
