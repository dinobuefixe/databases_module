# Session 06 in Next.js with Prisma: window functions and views

The tutorial's window function queries on a copy of Pagila (top N per group with `DENSE_RANK`, a running total, gaps with `LAG`) and the `daily_rentals` materialised view with a concurrent refresh.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | `npx prisma db pull` output trimmed to `film`, `rental` and `payment`. |
| `prisma/migrations/0_init/migration.sql` | Baseline of the existing tables, marked as applied and never run. |
| `prisma/migrations/1_daily_rentals/migration.sql` | The materialised view and its unique index, written by hand. |
| `src/app/api/films/longest-per-rating/route.ts` | `DENSE_RANK() OVER (PARTITION BY rating ORDER BY length DESC)`, filtered in an outer query. |
| `src/app/api/customers/[id]/payments/route.ts` | Running total with `SUM(amount) OVER (... ORDER BY payment_date)`. |
| `src/app/api/customers/[id]/rental-gaps/route.ts` | Time since the customer's previous rental with `LAG`. |
| `src/app/api/daily-rentals/route.ts` | Reads the materialised view. |
| `src/app/api/daily-rentals/refresh/route.ts` | `REFRESH MATERIALIZED VIEW CONCURRENTLY daily_rentals`. |

Everything here uses `$queryRaw`. Prisma's query API has no `OVER (...)` clause, and its schema cannot describe a materialised view, so the view lives in a migration written by hand. The baseline steps are the same as in session 04: `prisma migrate dev` would see the Pagila tables that no migration creates as drift and offer to reset the database, so this project applies migrations with `prisma migrate deploy`.

A few columns are cast in the SQL so that `$queryRaw` can return them as JSON: `DENSE_RANK()` and `count(*)` return `bigint` (`::int`), `rating` is a custom enum type (`::text`), and `gap` is an `interval`, which `$queryRaw` cannot read (`::text`, plus `gap_days` as a number).

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s06_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run db:baseline      # prisma migrate resolve --applied 0_init
npm run db:deploy        # prisma migrate deploy: creates daily_rentals
npm run dev
```

```bash
curl 'localhost:3000/api/films/longest-per-rating?top=2'
curl localhost:3000/api/customers/1/payments
curl localhost:3000/api/customers/1/rental-gaps
curl 'localhost:3000/api/daily-rentals?from=2022-05-24&days=10'
curl -X POST localhost:3000/api/daily-rentals/refresh
```

`longest-per-rating?top=2` returns more than two films for some ratings: three G films are 185 minutes long, and all three share position 1.

## Things to try

- In `longest-per-rating`, replace `DENSE_RANK` with `RANK` and then with `ROW_NUMBER`. Compare the positions of the tied G films with the table in the theory section.
- See that the materialised view is stale until refreshed. In `psql` (`docker compose exec postgres psql -U postgres -d s06_nextjs`):

  ```sql
  INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id)
  VALUES (now(), 1, 1, (SELECT min(staff_id) FROM staff));
  SELECT * FROM daily_rentals WHERE day = current_date;   -- 0 rows
  ```

  Then `curl -X POST localhost:3000/api/daily-rentals/refresh` and run the `SELECT` again.
- Drop the unique index (`DROP INDEX daily_rentals_day;`) and call the refresh endpoint: `CONCURRENTLY` now fails and says why. Recreate it with the statement in the migration.
- Remove the `ORDER BY payment_date` inside `OVER (...)` in the running total. Without an order, the frame is the whole partition and every row shows the customer's grand total.
- Try `WHERE pos <= 2` directly in the inner query and read the error: window functions are computed after `WHERE`.
