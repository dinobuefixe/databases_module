# Session 05 in Next.js with Prisma: joins, aggregation, subqueries and CTEs

The tutorial's ten business questions on a copy of Pagila. Each endpoint has a Prisma query API version (`?impl=orm`) and the tutorial's SQL through `$queryRaw` (`?impl=sql`). Both return the same rows, and the server logs every SQL statement so you can compare what Prisma sends with the SQL you would write.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | `npx prisma db pull` output trimmed to the columns the questions use. Read-only project, so no migrations. |
| `src/lib/prisma.ts` | Query logging with `log: [{ emit: "event", level: "query" }]` and `$on("query")`. |
| `src/lib/questions.ts` | The ten questions, ORM and SQL side by side. Start here. |
| `src/lib/respond.ts` | Picks the implementation from `?impl=` and returns `{ impl, count, rows }`. |
| `src/app/api/rentals-per-staff/route.ts` | Rentals per staff member per store (joins + `GROUP BY`). |
| `src/app/api/frequent-customers/route.ts` | Customers with more than 40 rentals (`HAVING`). |
| `src/app/api/rentals-per-customer/route.ts` | Rentals per customer, including customers with none (`LEFT JOIN`, `count(r.rental_id)`). |
| `src/app/api/films-without-inventory/route.ts` | Films with no copy in any store (`NOT EXISTS`). |
| `src/app/api/customers-without-rentals/route.ts` | Customers who never rented (`LEFT JOIN ... IS NULL`). |
| `src/app/api/duplicate-customer-names/route.ts` | Pairs of customers with the same name (self join). |
| `src/app/api/films-longer-than-average/route.ts` | Films longer than the average film (subquery in `WHERE`). |
| `src/app/api/films-above-rating-average/route.ts` | Films longer than the average of their rating (correlated subquery). |
| `src/app/api/customer-totals/route.ts` | Rentals and amount paid per customer (subqueries in `FROM`). |
| `src/app/api/above-average-spenders/route.ts` | Customers above the average spend (CTEs). |
| `scripts/compare.ts` | Runs both versions of every question and checks the rows are identical. |

## Where the ORM version is awkward

| Question | Prisma | Comment |
|----------|--------|---------|
| Rentals per staff | `staff.findMany` with `_count` and `orderBy: { rental: { _count: "desc" } }` | Natural. `_count` starts from `staff`, so it acts like a `LEFT JOIN`: without `where: { rental: { some: {} } }` it returns every staff member, most with 0 rentals. The SQL's `INNER JOIN` drops them. |
| More than 40 rentals | `rental.groupBy` with `having` | `groupBy` produces a real `GROUP BY ... HAVING`, but it cannot include a relation. The names need a second query (`WHERE customer_id IN (...)` with hundreds of parameters) and a merge in JavaScript. |
| Rentals per customer | `customer.findMany` with `_count` | Natural, and it keeps customers with 0 rentals. The log shows Prisma counts `rental` in a grouped subquery in `FROM` and `LEFT JOIN`s it with `COALESCE(..., 0)`. Nothing is counted per joined row, so the tutorial's `count(*)` column has no Prisma form and the SQL version leaves it out. |
| Films with no inventory | `film.findMany({ where: { inventory: { none: {} } } })` | Natural. Prisma generates `NOT EXISTS (...)`, the same anti-join as the tutorial. |
| Customers without rentals | `customer.findMany({ where: { rental: { none: {} } } })` | Same filter, same `NOT EXISTS`. Prisma does not write the `LEFT JOIN ... IS NULL` form; the result is the same. |
| Same-name customers | `customer.groupBy` with `having` + `findMany` + pairs in JavaScript | Prisma cannot join a model to itself on columns that are not a relation. Two queries and a loop replace the self join. |
| Longer than average | `film.aggregate` + `findMany` | No subqueries in `where`: the average is a first round trip. `length` is an `Int`, and Prisma silently sends 115.27 as 115 in an `Int` filter; with `gt` and whole lengths the films are the same. |
| Longer than the rating's average | `film.groupBy` by `rating` + `findMany` with one `OR` branch per rating | No correlated subqueries. `rating` is a PostgreSQL enum: Prisma returns its own names (`PG_13`), so the SQL casts to `text` and the ORM version maps the names back to `PG-13`. |
| Customer totals | `customer.findMany` with `_count` + `payment.groupBy` + merge | Prisma never joins `rental` and `payment` to `customer` in one query, so it cannot make the 1:N mistake from the tutorial. The schema has no `payment` relation, so the amounts are a second query. |
| Above average spend | `payment.groupBy` + average in JavaScript + `customer.findMany` | Prisma has no CTEs. Every customer's total is sent to the application, the average is computed there, and the names need another query. One SQL statement becomes three round trips. |

When a question is a report rather than "load these records", the SQL is usually shorter and cheaper. `$queryRaw` with a tagged template keeps it parameterised.

Small changes to the tutorial's SQL: `::int` on counts, because `count(*)` is a `bigint`, which `$queryRaw` returns as a JavaScript `BigInt` and JSON cannot serialise; a `customer_id` tie-breaker in `ORDER BY`, so both versions sort ties the same way and `compare` can check them row by row; `rating::text` in `films-above-rating-average`; and no `joined_rows` column in `rentals-per-customer` (see the table above).

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s05_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install          # also runs prisma generate
npm run compare
npm run dev
```

`npm run compare` prints:

```
same  rentals-per-staff          orm 2 rows, sql 2 rows
same  frequent-customers         orm 669 rows, sql 669 rows
same  rentals-per-customer       orm 999 rows, sql 999 rows
same  films-without-inventory    orm 42 rows, sql 42 rows
same  customers-without-rentals  orm 2 rows, sql 2 rows
same  duplicate-customer-names   orm 20 rows, sql 20 rows
same  films-longer-than-average  orm 489 rows, sql 489 rows
same  films-above-rating-average orm 497 rows, sql 497 rows
same  customer-totals            orm 999 rows, sql 999 rows
same  above-average-spenders     orm 592 rows, sql 592 rows
```

```bash
curl 'localhost:3000/api/rentals-per-staff?impl=orm'
curl 'localhost:3000/api/rentals-per-staff?impl=sql'
curl 'localhost:3000/api/frequent-customers?impl=orm'
curl 'localhost:3000/api/rentals-per-customer?impl=orm'
curl 'localhost:3000/api/films-without-inventory?impl=sql'
curl 'localhost:3000/api/customers-without-rentals?impl=sql'
curl 'localhost:3000/api/duplicate-customer-names?impl=orm'
curl 'localhost:3000/api/films-longer-than-average?impl=orm'
curl 'localhost:3000/api/films-above-rating-average?impl=orm'
curl 'localhost:3000/api/customer-totals?impl=orm'
curl 'localhost:3000/api/above-average-spenders?impl=orm'
```

Watch the terminal running `npm run dev`: each request prints its SQL, its parameters and its duration.

## Things to try

- Remove `where: { rental: { some: {} } }` from `rentalsPerStaff.orm` and run `npm run compare`. The ORM version now returns every staff member, which is the `LEFT JOIN` behaviour. Then change the SQL to a `LEFT JOIN` with `count(r.rental_id)` and get the same result. Why does `count(*)` give 1 instead of 0 for staff with no rentals?
- In `rentalsPerCustomer.sql`, replace `count(r.rental_id)` with `count(*)` and run `npm run compare`. It reports `DIFF`: customers 647 and 978 now have 1 rental in the SQL version and 0 in the ORM version.
- In `customerTotals.sql`, replace the two subqueries in `FROM` with plain `JOIN rental r` and `JOIN payment p` on `customer_id`, then `count(r.rental_id)::int` and `sum(p.amount)` with `GROUP BY c.customer_id`. Customer 1 goes from 66 rentals and 217.35 to 4,290 and 14,345.10, and `compare` reports `DIFF` with 997 SQL rows: the inner joins also drop the two customers with no rentals.
- Call `duplicate-customer-names` and `films-above-rating-average` with `impl=orm` and count the statements in the log against the single SQL statement.
- Call `above-average-spenders` with `impl=orm` and `impl=sql` and compare the durations in the log, and the number of statements.
- Replace `NOT EXISTS` in the SQL with `NOT IN (SELECT film_id FROM inventory)`. Same result here; now imagine one `inventory.film_id` were `NULL` (theory section).
- For each question, write down what one result row is (a staff member, a customer, a film) before reading the query, as the method in the theory suggests.
