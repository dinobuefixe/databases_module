# Runbook: restore the s10_nextjs PostgreSQL database

An example runbook entry for this project, in the shape the session 10 tutorial asks for. Commands run from this project's folder unless stated otherwise.

## When to use it

- Rows are missing or wrong in one or a few tables (a `DELETE` without the right `WHERE`, a faulty script): use **A. Restore one table**.
- The database is damaged or gone: use **B. Restore the whole database**.
- Before trusting a new backup routine, and once a month: use **C. Test the backup in a clean container**.

Do not use it for a problem that a backup cannot fix, such as a bug that keeps writing bad data: stop the writer first.

## Prerequisites

- Docker running, and `docker compose ps` at the repository root shows `postgres` as `healthy`.
- This project's `.env` in place (`cp .env.example .env`), and `npm install` done.
- A dump in `backups/`. List them with `ls -lt backups/`; the scripts use the newest one unless you pass a path.
- Write down the time of the incident and the time of the dump you will use. Everything written between the two is lost (the real RPO).

## A. Restore one table

1. Stop the application, so nothing writes to the table while you restore it.
2. Check what is missing: `npm run verify` against the last restored copy, or `curl localhost:3000/api/counts`.
3. Restore the table:

   ```bash
   npm run restore-table -- film_actor
   npm run restore-table -- film_actor backups/s10_nextjs_2026-10-07_143844.dump   # a specific dump
   ```

   The script runs `TRUNCATE film_actor`, then `pg_restore --data-only --single-transaction -t film_actor`. Rows written to that table after the dump are lost.
4. For a partitioned table (`payment`), restore the damaged partitions one by one: `npm run restore-table -- payment_p2022_03`. The script refuses the parent table and lists its partitions.
5. A table that other tables reference with foreign keys cannot be truncated on its own. Use B instead, or ask for help.

Expected time: under a second per Pagila table.

## B. Restore the whole database

1. Restore the newest dump into a new database and time it:

   ```bash
   npm run restore            # into s10_nextjs_restored
   ```

2. Compare it with the live database: `npm run verify`. The tables reported as `MISMATCH` should be exactly the ones you know were damaged; any other difference is data written after the dump, which the restore will lose.
3. Point the application at the restored database (`DATABASE_URL` in `.env`) or, during a planned window, rename the databases from `psql`:

   ```sql
   ALTER DATABASE s10_nextjs RENAME TO s10_nextjs_broken;
   ALTER DATABASE s10_nextjs_restored RENAME TO s10_nextjs;
   ```

4. Restore the roles if they were lost too: `docker compose exec -T postgres psql -U postgres < backups/roles_<stamp>.sql`. Errors for roles that already exist are expected.

Expected time: about half a second for Pagila (4.6 MB dump). Measure your own and write it here.

## C. Test the backup in a clean container

```bash
npm run clean-container-test
```

Starts a throwaway `postgres:18` container named `s10-nextjs-pgtest`, restores the dump, compares `SELECT count(*) FROM rental` with the live database, and removes the container. A backup that has never been restored is not a backup.

## Verify

- `npm run verify` compares the row count of every table (each partition separately) between `s10_nextjs` and `s10_nextjs_restored` and exits with code 1 on any difference.
- A known query: `curl localhost:3000/api/counts` should show `film_actor` 5462, `film_category` 2367 and `payment` 51061 on an untouched copy of Pagila.
- Start the application and call one endpoint.

## Who to tell

- Before starting: the people who use the application (the trainer, the group), with the expected downtime.
- After finishing: what happened, the dump used, the measured restore time, what was lost between the dump and the incident, and what will change so it does not happen again.
