# Session 08 in Next.js with Prisma: transactions and concurrency

The tutorial's `account` table and three ways to withdraw money: a naive read-then-write that loses updates, an atomic conditional `UPDATE`, and a row lock with `SELECT ... FOR UPDATE`. A script fires 50 concurrent withdrawals at the API to prove which ones keep the rule, and another provokes a deadlock and fixes it.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | The `account` model. |
| `prisma/migrations/*_account/migration.sql` | The table, plus `CHECK (balance >= 0)` added by hand. |
| `src/lib/withdraw.ts` | The three strategies. Start here. |
| `src/app/api/accounts/[id]/withdraw/route.ts` | `POST /api/accounts/:id/withdraw?strategy=naive\|atomic\|lock`. |
| `src/app/api/accounts/reset/route.ts` | `POST /api/accounts/reset`: accounts 1 and 2 back to a known balance. |
| `src/app/api/accounts/route.ts` | `GET /api/accounts`. |
| `scripts/concurrency.ts` | `npm run concurrency`: 50 simultaneous withdrawals of 10 from 100, for each strategy. |
| `scripts/deadlock.ts` | `npm run deadlock`: two transfers locking rows in opposite order, then in a fixed order. |
| `scripts/reset.ts` | `npm run reset`: the same reset from the command line. |

How each strategy maps to Prisma:

| Strategy | Prisma | SQL sent |
|----------|--------|----------|
| `naive` | `findUnique`, compute in JavaScript, `update` with the new value | `SELECT`, then `UPDATE account SET balance = 90` |
| `atomic` | `updateMany({ where: { id, balance: { gte: 10 } }, data: { balance: { decrement: 10 } } })` and check `count` | `UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10` |
| `lock` | interactive `$transaction` with `$queryRaw` `SELECT ... FOR UPDATE`, then `update` | `BEGIN; SELECT ... FOR UPDATE; UPDATE ...; COMMIT` |

`update` cannot take a condition on a non-unique column, which is why the atomic version uses `updateMany`: its `count` is the affected row count. Prisma has no API for `FOR UPDATE`, so the lock is a raw query inside the interactive transaction; every query on `tx` runs on the same connection, inside the same transaction.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s08_nextjs
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npx prisma migrate dev
npm run reset
npm run dev
```

In a second terminal:

```bash
curl -X POST localhost:3000/api/accounts/reset -H 'content-type: application/json' -d '{"balance": 100}'
curl -X POST 'localhost:3000/api/accounts/1/withdraw?strategy=atomic' -H 'content-type: application/json' -d '{"amount": 10}'
curl -X POST 'localhost:3000/api/accounts/1/withdraw?strategy=lock' -H 'content-type: application/json' -d '{"amount": 95}'   # 409
curl localhost:3000/api/accounts

npm run concurrency
npm run deadlock
```

`npm run concurrency` (the naive numbers change on every run):

```
naive    26 succeeded,  24 refused, 0 errors, final balance 0 -> RULE BROKEN: paid out 260, balance fell by 100
atomic   10 succeeded,  40 refused, 0 errors, final balance 0 -> rule holds
lock     10 succeeded,  40 refused, 0 errors, final balance 0 -> rule holds
```

The naive version handed out 260 while the balance only fell by 100: lost updates. The `CHECK` constraint did not stop it, because no single write made the balance negative.

`npm run deadlock`:

```
Locks in opposite order:
  A (1 -> 2): locked account 1
  B (2 -> 1): locked account 2
  A (1 -> 2): waiting for account 2
  B (2 -> 1): waiting for account 1
  A (1 -> 2): ABORTED, SQLSTATE 40P01: deadlock detected
  B (2 -> 1): committed
Locks in ascending id order:
  B (2 -> 1): locked account 1
  ...
  A (1 -> 2): committed
```

## Things to try

The two-session steps from the tutorial, in two terminals, each running `docker compose exec postgres psql -U postgres -d s08_nextjs` (run `npm run reset` first):

1. Lost update. Session A: `BEGIN; SELECT balance FROM account WHERE id = 1;` (100). Session B: `BEGIN; SELECT balance FROM account WHERE id = 1;` (100). A: `UPDATE account SET balance = 90 WHERE id = 1; COMMIT;`. B: `UPDATE account SET balance = 80 WHERE id = 1; COMMIT;`. `SELECT balance FROM account WHERE id = 1;` shows 80; it should be 70.
2. Fix 1. Repeat with `UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10;` in both sessions, without reading first. The result is 80 after starting from 100.
3. Fix 2. A: `BEGIN; SELECT balance FROM account WHERE id = 1 FOR UPDATE;`. B: the same `SELECT ... FOR UPDATE` waits. A: `UPDATE ...; COMMIT;`. B now returns, with A's new balance.
4. Deadlock. A: `BEGIN; SELECT * FROM account WHERE id = 1 FOR UPDATE;`. B: `BEGIN; SELECT * FROM account WHERE id = 2 FOR UPDATE;`. A: `SELECT * FROM account WHERE id = 2 FOR UPDATE;` (waits). B: `SELECT * FROM account WHERE id = 1 FOR UPDATE;`. One session gets `ERROR: deadlock detected` with `DETAIL` lines naming the two processes and the locks each one waits for. Prisma's error keeps the SQLSTATE and the message but not those detail lines, so `psql` is the place to read them.

Also try:

- `npm run concurrency -- 200`: with more requests, the naive version breaks further.
- In `src/lib/withdraw.ts`, remove `FOR UPDATE` from the lock strategy and run the concurrency script again.
- Lower `maxWait` in the lock strategy to `100` and run the script: requests that cannot start their transaction in time now fail with a 500. Holding locks and connections has a cost under load.
