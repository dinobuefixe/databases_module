# Session 11 in Next.js with Prisma: ORM and the N+1 problem

Maps Pagila's `customer` and `rental` tables with Prisma, reproduces the N+1 problem from the session 11 tutorial, fixes it with eager loading and counts the SQL statements each request sends.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | `Customer` and `Rental` trimmed from `npx prisma db pull`, with `@map` / `@@map` to the real column and table names. The `relationJoins` preview feature enables `relationLoadStrategy`. |
| `src/lib/prisma.ts` | Query log events (`log: [{ emit: "event", level: "query" }]` and `$on("query")`): every statement is printed when `LOG_SQL=true` and counted per request with `AsyncLocalStorage`. |
| `src/app/api/customers/route.ts` | `GET /api/customers`: a loop with one query per customer (N+1) against `include` with each load strategy, and `_count`. |
| `src/app/api/customers/top/route.ts` | `GET /api/customers/top`: the top customers by rentals, aggregated in the database in two ways. |
| `scripts/tutorial.ts` | The three blocks of the tutorial as a script, printing the number of queries for each. |

Prisma has no lazy loading: `customer.rentals` only exists if you asked for it with `include` or `select`. The N+1 in Prisma code is therefore a loop that calls `findMany` once per row, which is just as common.

| SQLAlchemy | Prisma |
|------------|--------|
| lazy relationship in a loop | `await prisma.rental.findMany(...)` inside a `for` loop |
| `selectinload(Customer.rentals)` | `include: { rentals: true }` with `relationLoadStrategy: "query"` (a second `SELECT ... WHERE customer_id IN (...)`) |
| `joinedload(Rental.customer)` | `relationLoadStrategy: "join"` (one `SELECT` with a `LEFT JOIN LATERAL` that builds JSON) |
| `func.count(...)` with `group_by` | `_count`, `groupBy`, or `orderBy: { rentals: { _count: "desc" } }` |
| `create_engine(..., echo=True)` | `log: [{ emit: "event", level: "query" }]` |

With the `relationJoins` preview feature on, `"join"` is the default strategy. This project passes `"query"` explicitly so you can compare both.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s11_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run tutorial
npm run dev
```

There are no migrations in this session: the tables already exist in Pagila and the app only reads them. `npm install` runs `prisma generate`.

```bash
curl 'localhost:3000/api/customers?limit=20&eager=false'                 # "queries": 21
curl 'localhost:3000/api/customers?limit=20&eager=true'                  # "queries": 2
curl 'localhost:3000/api/customers?limit=20&eager=true&strategy=join'    # "queries": 1
curl 'localhost:3000/api/customers?limit=20&eager=true&strategy=count'   # "queries": 1, no rental rows sent
curl 'localhost:3000/api/customers/top?limit=5'                          # groupBy, 2 queries
curl 'localhost:3000/api/customers/top?limit=5&via=relation'             # 1 query, but slower
```

Watch the terminal running `npm run dev`: each statement is printed with its duration.

## Things to try

- Call `eager=false` with `limit=200` and compare `queries` and `ms` with `eager=true`. With 20 rows the difference is small; with 200 it is not.
- `strategy=count` returns the same numbers without transferring a single rental row. When you only need a number, ask the database for the number.
- Compare the two versions of `/top`. `via=relation` is one query, but read the SQL in the response: Prisma counts the rentals of all 599 customers with a lateral subquery before sorting, which takes hundreds of milliseconds. `groupBy` sends the `GROUP BY ... ORDER BY count DESC LIMIT 5` you would write by hand, plus one query for the names. Fewer queries is not always faster; read the SQL.
- Copy one of the logged statements into `psql` with `EXPLAIN ANALYZE` in front of it.
- Add `include: { customer: true }` to a `prisma.rental.findMany` call (the N:1 direction) and look at the SQL for each strategy.
