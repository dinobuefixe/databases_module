# Session 08 in FastAPI: transactions and concurrency

The `account` table from the session 08 tutorial, a withdrawal endpoint with three strategies (the naive read-then-write that loses updates, the atomic conditional `UPDATE`, and `SELECT ... FOR UPDATE`), a script that fires concurrent requests at the API, and a deadlock demonstration with its fix.

| File | What it shows |
|------|---------------|
| `sql/001_account.sql` | `account(id, balance CHECK (balance >= 0))`. Created when the app starts. |
| `app/accounts.py` | `withdraw_naive` (read, compute, write), `withdraw_atomic` (one `UPDATE ... WHERE balance >= amount`, checked by row count), `withdraw_lock` (`SELECT ... FOR UPDATE`, then write). |
| `app/main.py` | `POST /accounts/{id}/withdraw?strategy=naive\|atomic\|lock`, `GET /accounts/{id}`, `POST /accounts/reset` (accounts 1 and 2 back to 100). |
| `scripts/concurrency.py` | Sends 50 withdrawals of 10 at the running API for each strategy and prints successes and the final balance. |
| `scripts/deadlock.py` | Two transfers in opposite directions that lock rows in opposite order: PostgreSQL aborts one, the script prints the error and retries. Then the same with a fixed lock order: no deadlock. |
| `tests/test_withdraw.py` | The tutorial's Python test: 50 concurrent withdrawals of 10 from 100, exactly 10 succeed. Passes for `atomic` and `lock`; the `naive` case is marked as an expected failure. |

`withdraw_naive` sleeps 50 ms between the read and the write. The sleep does not cause the bug; it makes the window wide enough that the lost update shows up on every run instead of now and then.

## Run it

From the root of the repository, start the engines and create this project's database:

```bash
docker compose up -d
./scripts/create-db.sh s08_fastapi
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
curl -X POST localhost:8000/accounts/reset
curl -X POST 'localhost:8000/accounts/1/withdraw?strategy=atomic' -H 'content-type: application/json' -d '{"amount": 10}'
curl -X POST 'localhost:8000/accounts/1/withdraw?strategy=lock' -H 'content-type: application/json' -d '{"amount": 95}'   # 409
curl localhost:8000/accounts/1
```

In a second terminal (`scripts.concurrency` needs the API running; the other two talk to the database directly):

```bash
uv run python -m scripts.concurrency
uv run python -m scripts.deadlock
uv run pytest -v
```

`scripts.concurrency` prints something like:

```
naive   succeeded=50  refused=0   final balance=70.0   money withdrawn=500  RULE BROKEN: lost update
atomic  succeeded=10  refused=40  final balance=0.0    money withdrawn=100  OK
lock    succeeded=10  refused=40  final balance=0.0    money withdrawn=100  OK
```

The naive version handed out 500 while the balance only dropped by 30, and the `CHECK` constraint did not notice: every value written was positive. Constraints protect the values, not the arithmetic between them.

## Things to try

The two-`psql`-session steps from the tutorial. Open two terminals at the repository root and run `docker compose exec postgres psql -U postgres -d s08_fastapi` in each. Reset first with `UPDATE account SET balance = 100 WHERE id = 1;`.

Lost update:

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

The final balance is 80. It should be 70.

- Fix 1: both sessions run `UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10;` instead of reading first. B's `UPDATE` waits for A's commit, then re-reads the row and subtracts from 90.
- Fix 2: both sessions run `BEGIN; SELECT balance FROM account WHERE id = 1 FOR UPDATE;`. B waits at the `SELECT` until A commits, then sees A's value.
- Deadlock: A runs `BEGIN; SELECT * FROM account WHERE id = 1 FOR UPDATE;`, B runs `BEGIN; SELECT * FROM account WHERE id = 2 FOR UPDATE;`, then A asks for row 2 and B for row 1. After about a second one of them gets `ERROR: deadlock detected`. Read the `DETAIL` lines: each process waits for a lock the other holds.

More:

- Run `uv run python -m scripts.concurrency --strategies naive --workers 1`. With one request at a time the naive version is correct: the bug only exists under concurrency, which is why tests by hand do not find it.
- Set `NAIVE_PAUSE_SECONDS = 0` in `app/accounts.py` and run the naive strategy several times. The rule still breaks, just not on every run.
- Remove `FOR UPDATE` from `withdraw_lock` and run `uv run pytest -v`.
- While session B waits in fix 2, open a third session and run `SELECT pid, locktype, mode, granted FROM pg_locks WHERE NOT granted;`. B is waiting for a `ShareLock` on A's transaction, the same wording as the deadlock `DETAIL`.
