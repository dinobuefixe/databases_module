# Session 08 in Django: transactions and concurrency

The `account` table from the session 08 tutorial with three ways to withdraw money: a naive read-then-write that loses updates, an atomic conditional `UPDATE`, and a row lock with `select_for_update()`. A command fires concurrent requests at the API to prove which ones hold, and another one provokes a deadlock and shows the fix.

| File | What it shows |
|------|---------------|
| `demo/models.py` | `Account` with `CheckConstraint(balance >= 0)`, the last line of defence. |
| `demo/withdraw.py` | `naive` (`get()`, subtract in Python, `save()`), `atomic` (`filter(balance__gte=amount).update(balance=F("balance") - amount)` and the returned row count), `lock` (`transaction.atomic()` + `select_for_update()`). |
| `demo/views.py` | `POST /accounts/<id>/withdraw?strategy=naive|atomic|lock`, `POST /accounts/reset`, `GET /accounts`. |
| `demo/management/commands/concurrency.py` | Resets account 1 to 100, sends 50 withdrawals of 10 at the running API, 20 at a time, for each strategy, and prints successes and the final balance. Exits with an error if `atomic` or `lock` do not give exactly 10 successes. |
| `demo/management/commands/deadlock.py` | Two threads transfer between accounts 1 and 2, locking them in opposite order; one gets `deadlock detected`. Then the same transfers locking both rows in ascending id order. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s08_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl -X POST localhost:8001/accounts/reset
curl -X POST 'localhost:8001/accounts/1/withdraw?strategy=naive' -d '{"amount": 10}'
curl -X POST 'localhost:8001/accounts/1/withdraw?strategy=atomic' -d '{"amount": 10}'
curl -X POST 'localhost:8001/accounts/1/withdraw?strategy=lock' -d '{"amount": 80}'
curl -X POST 'localhost:8001/accounts/1/withdraw?strategy=lock' -d '{"amount": 10}'   # 409 insufficient funds
curl localhost:8001/accounts
```

In a second terminal, with the server running:

```bash
uv run python manage.py concurrency
uv run python manage.py deadlock
```

A run of `concurrency` on the machine this was tested on:

```
naive   succeeded  31, refused  19, final balance    0.00  WRONG, 210 withdrawn but never subtracted
atomic  succeeded  10, refused  40, final balance    0.00  correct
lock    succeeded  10, refused  40, final balance    0.00  correct
```

The naive version handed out 310 from an account that held 100. The `CHECK` constraint did not stop it, because every write was a valid, non-negative balance: the bug is that writes overwrote each other.

## The lost update in two psql sessions

Open two terminals at the root of the repository, each with `docker compose exec postgres psql -U postgres -d s08_django`, and reset the balance with `curl -X POST localhost:8001/accounts/reset` (or `UPDATE account SET balance = 100 WHERE id = 1;`).

| Session A | Session B |
|-----------|-----------|
| `BEGIN;` | |
| `SELECT balance FROM account WHERE id = 1;` → 100 | |
| | `BEGIN;` |
| | `SELECT balance FROM account WHERE id = 1;` → 100 |
| `UPDATE account SET balance = 90 WHERE id = 1;` | |
| `COMMIT;` | |
| | `UPDATE account SET balance = 80 WHERE id = 1;` |
| | `COMMIT;` |

The final balance is 80; it should be 70. That is what `naive()` does: `save()` writes the value computed in Python.

Fix 1: both sessions run `UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10;` instead of reading first. Fix 2: both sessions run `SELECT balance FROM account WHERE id = 1 FOR UPDATE;`; session B waits at that line until A commits, then reads 90.

Deadlock: session A runs `BEGIN; SELECT * FROM account WHERE id = 1 FOR UPDATE;`, session B `BEGIN; SELECT * FROM account WHERE id = 2 FOR UPDATE;`, then A locks id 2 and B locks id 1. After about a second one of them gets `ERROR: deadlock detected` with the two `Process ... waits for ...` detail lines.

## Things to try

- Run `uv run python manage.py concurrency --strategy naive` several times. The number of successes changes every run; concurrency bugs are not reproducible by hand.
- Run it with `--workers 1`. The naive version is now correct: the bug only appears with concurrent requests.
- In `naive()`, wrap the body in `transaction.atomic()`. Does it fix anything? Why not, under `READ COMMITTED`?
- In `lock()`, remove `.select_for_update()` and run the concurrency command again.
- In `deadlock.py`, print the time each transfer took. The one that survives waits for PostgreSQL's `deadlock_timeout` (1 s by default) before the other is aborted.
