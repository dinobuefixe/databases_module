# Session 19 in Next.js with Prisma: delivery demo

A demo-ready app with one command per piece of evidence from the session 19 tutorial: the concurrency rule holding under load (session 08), Redis lost and rebuilt with the verification passing (session 16), and `EXPLAIN (ANALYZE, BUFFERS)` before and after indexes on a 2-million-row table (session 07). This README is written as the guide for running it from a clean clone.

| File | What it shows |
|------|---------------|
| `scripts/setup.ts` | `npm run setup`: baseline and migrations, `big_rental`, Redis sets. Safe to run twice. |
| `scripts/demo-concurrency.ts` | `npm run demo:concurrency`: 50 simultaneous withdrawals of 10 from 100, read-then-write against one conditional `UPDATE`. |
| `scripts/demo-rebuild.ts` | `npm run demo:rebuild`: verify, `FLUSHDB`, verify (fails), rebuild with timing, verify (passes). |
| `scripts/demo-explain.ts` | `npm run demo:explain`: full plans before and after the composite and the partial index, then a summary table. |
| `scripts/clean-clone-check.sh` | Clones a repository at a tag into a temporary folder, runs the steps below and times each one. |
| `prisma/migrations/1_account/` | The `account` table with `CHECK (balance >= 0)`. |
| `src/lib/withdraw.ts`, `src/lib/films-sets.ts` | The code each demo exercises, also used by the API. |
| `src/app/api/` | `GET /api/health`, `GET /api/accounts/{id}`, `POST /api/accounts/{id}/withdraw`, `GET /api/verify`. |

## Run it from a clean clone

You need Docker, Node.js 22 and Git. Nothing else is installed on your machine.

1. Clone the tag and start the engines, from the root of the repository:

   ```bash
   git clone --branch v1.0 <repository-url> databases_module
   cd databases_module
   cp .env.example .env
   docker compose up -d
   docker compose ps                      # wait until all three are healthy
   ./scripts/load-pagila.sh
   ./scripts/create-db.sh s19_nextjs --pagila
   ```

2. Set up this project:

   ```bash
   cd sessions/19-delivery-demo/nextjs
   cp .env.example .env                   # the passwords must match the root .env
   npm ci
   npm run setup                          # about 10 seconds; big_rental takes most of it
   ```

   `BIG_RENTAL_ROWS` in `.env` sets the size of `big_rental` (2,000,000 by default).

3. Run the demo, in this order:

   ```bash
   npm run demo:concurrency
   npm run demo:rebuild
   npm run demo:explain
   ```

4. Optionally, the API:

   ```bash
   npm run build && npm start
   curl localhost:3000/api/health
   curl localhost:3000/api/verify
   ```

## What each demo prints

`demo:concurrency`:

```
naive     50 of 50 succeeded, final balance   90, money handed out 500  RULE BROKEN
atomic    10 of 50 succeeded, final balance    0, money handed out 100  RULE HOLDS
```

The naive numbers change from run to run; that is the point. The exit code is 0 only when the atomic version holds the rule.

`demo:rebuild` (the tutorial's `FLUSHALL` is `FLUSHDB` on database 3 here, because the course's Redis is shared by every project; in your group project use `FLUSHALL`):

```
before           ...  0 mismatches  OK
after FLUSHDB    ...  997 mismatches  FAIL
rebuild          999 customers in ~50 ms (one query, one pipeline)
after rebuild    ...  0 mismatches  OK
```

`demo:explain` ends with a table like this (times vary by machine):

| case | before | after |
|------|--------|-------|
| `big_rental_customer_rented` | Parallel Seq Scan, ~30 ms | Index Scan, ~0.03 ms |
| `big_rental_open` | Parallel Seq Scan, ~18 ms | Index Only Scan, ~4 ms |

## Check the clean clone automatically

```bash
bash scripts/clean-clone-check.sh <repository-url> v1.0 sessions/19-delivery-demo/nextjs
```

It clones into a temporary folder, runs `cp .env.example .env`, `npm ci`, `npm run setup`, `npm run build`, starts the app on port 3100 (`CHECK_PORT`) and waits for `/api/health`, then prints the time for each step. It reuses the engines and the database that are already running; it never starts a second set of containers. `KEEP=1` keeps the clone for inspection. For your group project, pass the repository URL and tag, and edit the steps in the script to match your README.

## Things to try

- Rehearse the 10 minutes with a timer. Say what the audience should look at before each command runs, not after.
- Run `clean-clone-check.sh` before tagging. When the clone was tested for this README, `src/lib/` and every `migration.sql` were missing from it: a global Git ignore file on the author's machine excluded `lib/` and `*.sql`. Run `git ls-files` and `git check-ignore -v <file>` on anything the clone cannot find.
- Run `npm run demo:explain` twice. The second "before" is faster: the table pages are now in memory (`shared hit` instead of `shared read` on the `Buffers:` lines).
- Change the composite index to `(rented_at DESC, customer_id)` in `scripts/demo-explain.ts` and explain why the plan changes.
