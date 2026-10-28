# Session 10 in FastAPI: backup and restore

The session 10 tutorial wrapped in Python scripts: a custom-format `pg_dump` and a `pg_dumpall --roles-only`, a timed restore into a new database, a single-table restore, a simulated disaster, a row-count verification between two databases, and a restore into a clean throwaway container. The scripts call `docker compose exec -T postgres ...`, the same commands as the tutorial.

| File | What it shows |
|------|---------------|
| `scripts/backup.py` | `pg_dump -Fc` into `backups/s10_fastapi_<date>_<time>.dump` and `pg_dumpall --roles-only` into `backups/roles_<date>_<time>.sql`. |
| `scripts/restore.py` | Drops and recreates `s10_fastapi_restored`, restores the newest dump into it with `pg_restore --no-owner` and prints the time taken. |
| `scripts/restore_table.py` | Restores one table into `s10_fastapi`: `TRUNCATE`, then `pg_restore --data-only -t` for the table and its partitions. `--clean` runs the tutorial's `pg_restore --clean -t` instead (see below). |
| `scripts/simulate_disaster.py` | Deletes rows from `payment`, `film_actor` and `film_category` in `s10_fastapi`. |
| `scripts/verify.py` | Compares the row count of every table in two databases and exits with 1 on any difference. |
| `scripts/clean_container_test.py` | Starts a throwaway `postgres:18` container (`s10-fastapi-pgtest`), restores the newest dump into it, counts rentals, and removes the container. |
| `scripts/common.py` | Paths, the `docker compose exec` wrapper, and the check that refuses any database not named `s10_fastapi*`. |
| `app/main.py` | `GET /counts`, `GET /compare` (the same check as `verify.py`) and `GET /backups`. |
| `docs/runbook.md` | An example runbook entry: when to use it, prerequisites, commands, verification, expected time, who to tell. |
| `.gitignore` | `backups/`: dumps hold all the data and the roles file holds password hashes. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s10_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync

uv run python -m scripts.backup
uv run python -m scripts.restore                       # into s10_fastapi_restored, timed
uv run python -m scripts.verify                        # s10_fastapi against s10_fastapi_restored: all match, exit 0
uv run python -m scripts.simulate_disaster
uv run python -m scripts.verify; echo "exit code $?"   # 3 tables differ, exit 1
uv run python -m scripts.restore_table payment
uv run python -m scripts.restore_table film_actor
uv run python -m scripts.restore_table film_category
uv run python -m scripts.verify                        # all match again
uv run python -m scripts.clean_container_test
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

The API reads the same numbers:

```bash
uv run uvicorn app.main:app --reload --port 8000
curl localhost:8000/backups
curl localhost:8000/counts
curl 'localhost:8000/counts?db=s10_fastapi_restored'
curl localhost:8000/compare
```

## The single-table restore and Pagila

Why does the tutorial not use `pg_restore --clean -t payment`? Try it:

```bash
uv run python -m scripts.restore_table payment --clean
```

On this Pagila it fails, for two reasons. `--clean` starts with `DROP TABLE payment`, which PostgreSQL refuses because views (`sales_by_store`, `sales_by_film_category`) and a materialised view depend on it. And `payment` is partitioned: its rows live in `payment_p2022_01` to `payment_p2026_07`, so `-t payment` selects a table that holds no rows itself. `pg_restore` reports two errors and the table is left as it was.

The default mode of `restore_table.py` avoids both problems: it keeps the table definition, empties it with `TRUNCATE`, and restores only the data, naming every partition with its own `-t`. That works for tables that no other table references with a foreign key, which is why `simulate_disaster.py` damages `payment`, `film_actor` and `film_category`. For a table like `customer`, restore the whole dump into a new database and copy the rows you need across.

## Things to try

- Run the tutorial commands by hand from the repository root and compare them with the scripts:

  ```bash
  docker compose exec -T postgres pg_dump -U postgres -Fc s10_fastapi > /tmp/s10.dump
  docker compose exec -T postgres pg_restore -l < /tmp/s10.dump | head -30
  ```

  `pg_restore -l` lists the archive's contents: one entry per table, partition, index and constraint.
- Leave out `-T` in `docker compose exec` and dump again. Compare the file sizes and try to restore it.
- Add `-j 4` to the `pg_restore` call in `scripts/restore.py`. Parallel restore needs a file it can seek in, not stdin: copy the dump into the container first (`docker compose cp`) and point `pg_restore` at the path.
- Open `backups/roles_*.sql`. It contains every role on the server with its password hash, which is why it must never reach Git.
- Take a backup, then add a payment: `INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date) VALUES (1, 1, 1, 9.99, '2026-07-15');`. Run `simulate_disaster` and `restore_table payment`: the new payment is gone, because it was written after the backup. That gap is the real RPO. Restore `film_actor` and `film_category` as well before you move on.
- In your own environment (not this shared one), the full rehearsal is `docker compose down -v`, `docker compose up -d`, load nothing, and restore from `backups/`. Here, `clean_container_test.py` gives the same proof with a container of its own.
