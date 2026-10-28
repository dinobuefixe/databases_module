# Session 19 in Django: a demo you can run from a clean clone

A demo-ready app for the session 19 technical discussion, built from pieces of sessions 07, 08 and 16. Each demo is one management command that prints its own before and after evidence, and `scripts/clean-clone-check.sh` checks that a fresh clone of a tag gets there by following this README alone.

| File | What it shows |
|------|---------------|
| `demo/management/commands/setup_demo.py` | Prepares everything: account 1 with 100, `big_rental` with 2,000,000 rows (`setseed`, so every clone gets the same data), the Redis sets. |
| `demo/management/commands/demo_concurrency.py` | 50 concurrent withdrawals of 10 from 100 with three strategies: `naive` breaks the rule, `atomic` and `lock` keep it. |
| `demo/management/commands/demo_rebuild.py` | `FLUSHDB`, verification failing, rebuild from PostgreSQL with timing, verification passing (exit code 1 if it does not). |
| `demo/management/commands/demo_explain.py` | `EXPLAIN (ANALYZE, BUFFERS)` for the two session 07 queries, without and then with their index, and a summary of the times. |
| `demo/withdraw.py` | The three withdrawal strategies (session 08). |
| `demo/models.py` | `Account` with `CHECK (balance >= 0)`, `BigRental`, and the two indexes as Django `Index` objects (one composite with `DESC`, one partial with `condition`). |
| `demo/derived.py` | `customer:{id}:films` rebuild and verify (session 16). |
| `demo/views.py` | `GET /health`, `GET /accounts/{id}`, `POST /accounts/{id}/withdraw`, `GET /customers/{id}/films`. |
| `scripts/clean-clone-check.sh` | Clones a repository at a tag into a temporary folder, runs the steps below and reports the time taken. |

## Run it from a clean clone

You need Docker, Git and [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 or later if it is missing). From an empty folder:

```bash
git clone --branch v1.0 <repository-url> databases_module
cd databases_module
cp .env.example .env
docker compose up -d --wait
./scripts/create-db.sh s19_django --pagila
cd sessions/19-delivery-demo/django
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py setup_demo          # about 2 s on a laptop; --rows 200000 for a smaller table
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

If a step needs anything not written here, the README is wrong: fix it and tag again.

## The three demos

```bash
uv run python manage.py demo_concurrency    # naive: 50 succeed, balance about 50; atomic and lock: 10 succeed, balance 0
uv run python manage.py demo_rebuild        # 997 customers differ, rebuild about 0.5 s, all 997 match
uv run python manage.py demo_explain        # composite index: about 30 ms -> 0.1 ms; partial index: about 25 ms -> 4 ms
```

Each command can be run on its own and in any order; `demo_concurrency` resets the account each time. `demo_concurrency --strategy naive` exits with code 1, so you can also show the failure as a failing command.

The API, for questions during the discussion:

```bash
uv run python manage.py runserver 8001
curl localhost:8001/health
curl -X POST localhost:8001/accounts/1/withdraw -H 'content-type: application/json' -d '{"amount": 10}'
curl localhost:8001/customers/1/films
```

## Check the clean clone automatically

```bash
scripts/clean-clone-check.sh https://github.com/<you>/<repo>.git v1.0
```

It clones into a temporary folder, starts the engines, creates `s19_django_clean` (dropped and recreated each time), installs, migrates, runs `setup_demo` and the three demos, and prints the elapsed time at each step. Set `SKIP_ENGINES=1` if the engines are already running, `ROWS=200000` for a faster run, `KEEP=1` to look at the folder afterwards.

## FLUSHDB instead of FLUSHALL

The tutorial's demo is `FLUSHALL`, then the rebuild. The Redis server in this repository is shared by every session's projects, so `demo_rebuild` uses `FLUSHDB`, which only empties database 2. In your group project, with a Redis of your own, show `FLUSHALL`.

## Things to try

- Rehearse the 10 minutes with a timer: run the three demos, and for each one say in one sentence what the evidence proves.
- Run `demo_explain` twice and compare the `Buffers` lines of the two "before" plans. Most pages are still `read`, not `hit`: a sequential scan of a table larger than a quarter of `shared_buffers` uses a small ring of buffers so that it does not push everything else out of the cache, and the pages come from the operating system's cache instead. The times change by a few milliseconds between runs; the gap with the index does not.
- Replace `VACUUM ANALYZE` with `ANALYZE` in `setup_demo`, run it again, then `demo_explain`. The partial index plan changes from `Index Only Scan` to a bitmap scan and is no longer faster. Find out why before someone asks you.
