# Session 10 in Django: backup and restore

The session 10 tutorial as management commands: a custom-format backup into `backups/`, a timed restore into a new database, restoring the rows of single tables, a simulated accident, a row-count comparison that fails on any difference, and a restore into a throwaway `postgres:18` container.

| File | What it shows |
|------|---------------|
| `demo/pg.py` | Runs `pg_dump`, `pg_restore`, `psql`, `createdb` and `dropdb` with `docker compose exec -T postgres`, as in the tutorial, and refuses any database that is not this project's. |
| `demo/management/commands/backup.py` | `pg_dump -Fc` into `backups/s10_django_<timestamp>.dump` and `pg_dumpall --roles-only` into `backups/roles_<timestamp>.sql`. |
| `demo/management/commands/restore.py` | Recreates `s10_django_restored` and restores the latest dump with `--no-owner`, printing the time. |
| `demo/management/commands/restore_table.py` | Empties the given tables and loads their rows from the dump (`pg_restore --data-only -t`), in one transaction. |
| `demo/management/commands/simulate_disaster.py` | Deletes rows from `film_actor`, `film_category` and `payment` in `s10_django` only. |
| `demo/management/commands/verify.py` | Exact row count of every table in two databases (default `s10_django` and `s10_django_restored`); exit code 1 on any mismatch. |
| `demo/management/commands/clean_container_test.py` | Starts `s10-django-pgtest` (`postgres:18`, no volume), restores the latest dump, runs the tutorial's `SELECT count(*) FROM rental`, compares every table with `s10_django`, and stops the container. |
| `docs/runbook.md` | An example runbook for restoring deleted rows in this database. |

The commands call the PostgreSQL tools inside the container instead of reimplementing them: shell tools are the right tool for backups, and Django is only the entry point. `backups/` and `*.dump` are in the repository's `.gitignore`. The roles file contains password hashes, so it must never be committed either.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s10_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`. There are no models or migrations: the project only runs commands.

```bash
uv run python manage.py backup
uv run python manage.py restore                  # into s10_django_restored, about 0.5 s here
uv run python manage.py verify                   # 0 mismatches, exit code 0

uv run python manage.py simulate_disaster
uv run python manage.py verify; echo $?          # 4 mismatches, exit code 1
uv run python manage.py restore_table film_actor film_category payment_p2022_01 payment_p2022_02
uv run python manage.py verify; echo $?          # 0 mismatches, exit code 0

uv run python manage.py clean_container_test
```

`verify` lists `payment_p2022_01` and `payment_p2022_02`, not `payment`: a partitioned table keeps its rows in its partitions. `restore_table payment` finds no data in the dump and says so.

## Things to try

- Try the tutorial's other single-table restore on `s10_django_restored`: `docker compose exec -T postgres pg_restore -U postgres -d s10_django_restored --clean -t film_actor < backups/<file>.dump`. Read why `DROP TABLE` fails. Then run it with `-t payment_p2022_01` (no views depend on a partition) and compare `\d payment_p2022_01` before and after: `-t` brings back the table and its data, but not its indexes, its foreign keys or its place in `payment`. `SELECT count(*) FROM payment WHERE payment_date < '2022-02-01'` now returns 0, although the partition holds 723 rows.
- Run `simulate_disaster`, then `backup`, then `restore` and `verify`. The new backup already contains the damage: which backup do you need, and what would you lose between it and the accident?
- Restore with timing for different formats: `pg_dump -Fp` (plain SQL, restored with `psql`) and `-Fd` with `pg_restore -j 4`. Directory format needs a path inside the container, for example `docker compose exec postgres pg_dump -U postgres -Fd -j 4 -f /tmp/s10 s10_django`.
- Open `backups/roles_<timestamp>.sql` and find the `ALTER ROLE ... PASSWORD` lines. Where should this file be stored?
- `uv run python manage.py verify s10_django pagila` is refused. Why does the command check database names on a shared server?

In your own environment the tutorial's real disaster test is `docker compose down -v` (it deletes the volumes) followed by `docker compose up -d`, `./scripts/load-pagila.sh` or `createdb`, and a restore. Do not run it on a server you share with others; `clean_container_test` gives the same proof with a container of its own.
