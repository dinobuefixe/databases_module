# Runbook: restore rows deleted by mistake in s10_django

An example runbook for this project's database. It follows the session 10 checklist: when to use it, prerequisites, exact commands, how to verify, expected time and who to tell.

## When to use it

Rows are missing from one or a few tables of `s10_django` (a `DELETE` with the wrong `WHERE`, a bad script), the rest of the database is fine, and there is a backup taken before the mistake. If the whole database is damaged or gone, use "Full restore" below instead.

Anything written to those tables after the backup was taken is lost by this procedure. Check the time of the backup against the time of the mistake before you start: that gap is the real RPO.

## Prerequisites

- The engines are running: `docker compose ps` (from the root of the repository) shows `postgres` healthy.
- In `sessions/10-backup-restore/django`, `.env` exists and `uv sync` has been run.
- At least one dump in `backups/`: `ls -lt backups/*.dump`. The commands use the newest one unless you pass `--dump backups/<file>.dump`.
- You know which tables lost rows. `uv run python manage.py restore` followed by `uv run python manage.py verify` lists them (see step 1).
- Writes to the affected tables are stopped (application paused or in maintenance), so nothing new is lost when the table is emptied.

## Steps

1. Restore the backup into a separate database and compare, to see exactly which tables differ:

   ```bash
   uv run python manage.py restore            # into s10_django_restored, prints the time taken
   uv run python manage.py verify             # exit code 1 and the list of tables that differ
   ```

2. Restore the rows of those tables into the live database. A partitioned table keeps its rows in the partitions, so for `payment` name the partitions that differ:

   ```bash
   uv run python manage.py restore_table film_actor film_category payment_p2022_01 payment_p2022_02
   ```

   Each table is emptied and reloaded from the dump in one transaction. If it fails, the tables are left as they were.

3. Verify (next section).

## Verify

```bash
uv run python manage.py verify             # must print 0 mismatches and exit with code 0
echo $?
```

Then a known query, compared with the value before the incident:

```bash
docker compose exec -T postgres psql -U postgres -d s10_django -c "SELECT count(*) FROM film_actor WHERE actor_id <= 50;"
```

## Full restore

When the database itself is lost, restore the dump into `s10_django_restored`, verify it, and point `DATABASE_URL` at it, or recreate `s10_django` from the repository root with `./scripts/create-db.sh s10_django --reset` and restore into it with `pg_restore --no-owner`. To prove a dump works without anything from your setup, run `uv run python manage.py clean_container_test`.

## Expected time

Measured on the copy of Pagila used in the module (about 4.5 MB as a custom-format dump): full restore under 1 s, `restore_table` for four tables under 1 s, clean container test about 3 s including starting the container. Re-measure when the data grows and update this line.

## Who to tell

Before step 2: whoever owns the application, so writes can be paused. After verifying: the same people, with the time of the backup used, the tables restored and the data written between the backup and the incident that could not be recovered.
