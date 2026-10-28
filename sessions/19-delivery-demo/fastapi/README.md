# Session 19 in FastAPI: a demo you can run from a clean clone

A demo-ready app with one `make` target per piece of evidence: concurrent withdrawals with and without the fix (session 08), Redis emptied, verified, rebuilt and verified again (session 16), and `EXPLAIN (ANALYZE, BUFFERS)` before and after the indexes on a 2,000,000-row table (session 07). This README is written as the guide for running it from a fresh clone.

| File | What it shows |
|------|---------------|
| `Makefile` | `install`, `db`, `setup`, `run`, `demo-concurrency`, `demo-rebuild`, `demo-explain`, `demo`. |
| `app/main.py` | `GET /health`, `PUT /accounts/{id}`, `POST /accounts/{id}/withdraw?strategy=naive\|atomic`, `GET /verify`. |
| `app/films_sets.py` | Rebuild and verification of the `customer:{id}:films` Redis sets. |
| `scripts/setup.py` | `account` table, `big_rental` (`setseed(0.1)`, `BIG_RENTAL_ROWS` rows, then `VACUUM ANALYZE`), Redis sets. Safe to run again. |
| `scripts/demo_concurrency.py` | 50 withdrawals of 10 from 100 at once, `naive` then `atomic`, with the totals that prove or break the rule. |
| `scripts/demo_rebuild.py` | Verify, `FLUSHDB`, verify (fails), rebuild with timing, verify (passes). |
| `scripts/demo_explain.py` | Drops the indexes, runs the two tutorial queries, creates the composite and partial indexes, runs them again, prints time, scan type and buffers. |
| `scripts/clean-clone-check.sh` | Clones a repository at a tag into a temporary folder, runs these setup steps there and reports the time of each. |

## Run it from a clean clone

You need Docker, [uv](https://docs.astral.sh/uv/), `make` and `git`. uv downloads a suitable Python (3.12 or newer) if the machine has none.

```bash
git clone --branch v1.0 <repository-url> databases-module
cd databases-module
cp .env.example .env
docker compose up -d --wait
./scripts/load-pagila.sh

cd sessions/19-delivery-demo/fastapi
make install        # uv sync, and .env from .env.example
make setup          # creates s19_fastapi from Pagila, then account, big_rental, Redis sets
make run            # API on http://localhost:8000; leave it running
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`. The other targets run their commands with `uv run`, so there is no virtual environment to activate.

In a second terminal, in the same folder:

```bash
make demo-concurrency
make demo-rebuild
make demo-explain
```

`make demo` runs the three in order. Each script exits with a non-zero code if the rule it demonstrates does not hold.

## What each demo prints

`make demo-concurrency`:

```
NAIVE: 50 withdrawals of 10 from 100
  succeeded  50   refused   0   other 0
  paid out     500   balance  60.00   paid out + balance = 560.00
  rule holds: NO, money was created

ATOMIC: 50 withdrawals of 10 from 100
  succeeded  10   refused  40   other 0
  paid out     100   balance   0.00   paid out + balance = 100.00
  rule holds: YES
```

The naive numbers change from run to run; the atomic ones never do.

`make demo-rebuild`:

```
1. before                    keys=  997  mismatches=   0  PASS
   FLUSHDB on Redis database 1
2. after FLUSHDB             keys=    0  mismatches= 997  FAIL
   rebuilt 999 customer sets from PostgreSQL in 0.04 s
3. after rebuild             keys=  997  mismatches=   0  PASS
```

The tutorial uses `FLUSHALL`. The Redis in this repository is shared by several projects on different logical databases, so the demo runs `FLUSHDB`, which empties only database `/1`. In a group project with its own Redis, `FLUSHALL` is the honest version of the demo.

`make demo-explain` (times from one run; yours will differ):

```
big_rental: 2,000,000 rows

last 10 rentals of customer 42
  before     19.41 ms  Parallel Seq Scan on big_rental                          Buffers: shared hit=4148 read=8664
  after       0.02 ms  Index Scan using big_rental_customer_rented on big_rent  Buffers: shared hit=10 read=3

open rentals older than 30 days
  before     19.84 ms  Parallel Seq Scan on big_rental                          Buffers: shared hit=4354 read=8382
  after       3.99 ms  Index Only Scan using big_rental_open on big_rental      Buffers: shared hit=1 read=161

sizes: big_rental 100 MB, big_rental_customer_rented 60 MB, big_rental_open 1336 kB
```

The composite index turns a scan of the whole table (about 12,800 pages) into a read of a few pages. The partial index holds only the open rentals, about 60,000 of the 2,000,000 rows, so it is 1.3 MB against 60 MB for the composite one. The count needs only `rented_at`, which is in the index, so PostgreSQL answers with an Index Only Scan (`Heap Fetches: 0` in the full plan) and never visits the table. That works because `make setup` runs `VACUUM ANALYZE` after creating the table, which fills the visibility map; on a live table autovacuum does the same. Without it, PostgreSQL has to visit the table for each of the 60,000 rows, which are spread over most of its pages, and the gain mostly disappears. Say that in the demo; it is the kind of question the trainer asks. Run `uv run python -m scripts.demo_explain --plans` for the full plans.

## Rehearse the clean clone

`scripts/clean-clone-check.sh` repeats the steps above in a temporary folder and times them:

```bash
./scripts/clean-clone-check.sh https://github.com/<you>/<repo>.git v1.0
```

One run on a machine where the engines were already up and Pagila already loaded (`START_ENGINES=0`):

```
git clone v1.0                            1 s
copy .env.example to .env (root)          0 s
load Pagila                               1 s
make install                              0 s
make setup                                6 s
API answers /health                       3 s
Clean clone check passed in 11 s
```

`make install` takes no time here because uv already had every package in its cache. On an empty machine, add the image downloads, `docker compose up`, the Pagila load and the package downloads.

The clone uses the same Compose project name as your working copy, so it talks to the same containers and volumes. To test on a really empty machine, run it there, or stop your working copy's engines first. On a machine where the engines are already running and shared, use `START_ENGINES=0` to skip `docker compose up`.

## Things to try

- Change `BIG_RENTAL_ROWS` in `.env` to 200000 and run `uv run python -m scripts.setup --force-big-rental`, then `make demo-explain`. With a small table the gap shrinks, which is why the tutorial uses 2,000,000 rows.
- Remove `time.sleep(0.01)` from the naive branch in `app/main.py` and run `make demo-concurrency` a few times. Count how often the naive run still breaks the rule: a demo that depends on timing needs a test that does not.
- Time yourself: the three demos together should fit in under three minutes, leaving the rest of the 10 minutes for explaining them.
- Run the clean clone check and write down every step you had to do by hand. Each one is a missing line in this README.
