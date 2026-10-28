# Runbook: restore the s10_fastapi database from the latest backup

An example of a runbook entry. Write it so that someone who has never seen the project can follow it under pressure.

## When to use it

- The database is gone or unusable (volume lost, disk failure, a migration that destroyed the schema).
- Data was deleted or changed by mistake in many tables. For one table, see "Restore a single table" below.

Do not use it to undo a single bad row: fix that row by hand from the restored copy instead.

## Prerequisites

- Docker running, and the engines up: `docker compose up -d` from the repository root, `docker compose ps` shows `postgres` as `healthy`.
- A dump in `sessions/10-backup-restore/fastapi/backups/` named `s10_fastapi_<date>_<time>.dump`. Note its date and time: everything written after it is lost (the real RPO).
- [uv](https://docs.astral.sh/uv/), a `.env` copied from `.env.example`, and `uv sync` run once in the project folder.

## Steps

All commands run in `sessions/10-backup-restore/fastapi/`.

1. Stop the application so nothing writes while you restore.
2. Restore the latest dump into a new database, without touching the damaged one:

   ```bash
   uv run python -m scripts.restore
   ```

   It prints the time taken. With the `--file` option you can pick an older dump.
3. Verify the restored database (next section).
4. Swap the databases as the superuser in `psql`, keeping the damaged one for investigation:

   ```sql
   ALTER DATABASE s10_fastapi RENAME TO s10_fastapi_damaged;
   ALTER DATABASE s10_fastapi_restored RENAME TO s10_fastapi;
   ```

   `RENAME` fails while sessions are connected to the database; stop them first.
5. On a new server, restore the roles first: `docker compose exec -T postgres psql -U postgres < sessions/10-backup-restore/fastapi/backups/roles_<date>.sql` from the repository root. On the existing server, the roles are still there and this step is skipped.
6. Start the application and check that `GET /counts` answers with the expected row counts.

## Restore a single table

For a table that no other table references with a foreign key (`payment`, `film_actor`, `film_category`):

```bash
uv run python -m scripts.restore_table payment
```

It empties the table and reloads its rows from the dump. Rows added since the backup are lost.

## Verify

- Row counts of every table, restored copy against the damaged one or against the counts recorded at backup time:

  ```bash
  uv run python -m scripts.verify s10_fastapi s10_fastapi_restored
  ```

  Exit code 0 means every table matches. After a disaster, the tables that were damaged are expected to differ; every other table must match.
- A known query with a known answer: `SELECT count(*) FROM rental;` returns 51,805 on this data set.

## Expected time

About 0.5 s for the restore of this 4.6 MB dump on a laptop, measured with `scripts.restore`. Measure again whenever the database grows, and update this line.

## Who to tell

- Before starting: the team channel, with the time of the incident and the dump you are going to use.
- After finishing: the same channel, with the restore time, the verification result and what was lost between the backup and the incident.
