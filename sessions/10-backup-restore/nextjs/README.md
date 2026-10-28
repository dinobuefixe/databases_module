# Session 10 in Next.js with Prisma: backup and restore

The tutorial's backup and restore steps as npm scripts: a timestamped `pg_dump`, a timed restore into a new database, a single-table restore, a simulated disaster, a row-count verification that fails on any difference, and a restore into a clean throwaway container. `docs/runbook.md` is an example runbook for this project.

| File | What it shows |
|------|---------------|
| `scripts/shell.ts` | Runs `docker compose exec -T postgres ...` from the repository root, with files as stdin or stdout (`<` and `>` in the shell). |
| `scripts/backup.ts` | `npm run backup`: `pg_dump -Fc` and `pg_dumpall --roles-only` into `backups/` (git-ignored). |
| `scripts/restore.ts` | `npm run restore`: the newest dump into `s10_nextjs_restored`, with the time `pg_restore` took. |
| `scripts/restore-table.ts` | `npm run restore-table -- <table>`: `TRUNCATE`, then `pg_restore --data-only -t <table>`. |
| `scripts/simulate-disaster.ts` | `npm run simulate-disaster`: deletes rows from `film_actor`, `film_category` and `payment` in this project's database. |
| `scripts/verify.ts` | `npm run verify`: compares the row count of every table in two databases; exit code 1 on a mismatch. |
| `scripts/clean-container-test.ts` | `npm run clean-container-test`: restores into a throwaway `postgres:18` container and compares a count. |
| `src/app/api/counts/route.ts` | `GET /api/counts`: Prisma counts of the damaged tables, to watch the loss and the recovery. |
| `docs/runbook.md` | When to restore, prerequisites, commands, verification, expected time, who to tell. |

Prisma has no part in the backup itself: dumps work on the whole database, below any ORM. The Next.js app only shows the counts. The scripts use Node's `child_process` to call the same commands as the tutorial, so you can read each command in the code.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s10_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run dev     # optional: for GET /api/counts
```

The rehearsal, in a second terminal:

```bash
npm run backup
npm run restore
npm run verify                         # 0 mismatches
curl localhost:3000/api/counts
npm run simulate-disaster
curl localhost:3000/api/counts         # fewer rows
npm run verify                         # 4 mismatches, exit code 1
npm run restore-table -- film_actor
npm run restore-table -- film_category
npm run restore-table -- payment       # refused: payment is partitioned, lists the partitions
npm run restore-table -- payment_p2022_03
npm run restore-table -- payment_p2022_04
npm run verify                         # 0 mismatches
npm run clean-container-test
```

Output of the main steps:

```
backups/s10_nextjs_2026-10-07_143844.dump  4.6 MB in 0.53 s
pg_restore finished in 0.45 s (exit code 0)
69 tables compared between s10_nextjs and s10_nextjs_restored: 0 mismatches

DELETE 1327  DELETE FROM film_actor WHERE actor_id <= 50
DELETE 447   DELETE FROM film_category WHERE category_id IN (1, 2, 3)
DELETE 5260  DELETE FROM payment WHERE payment_date >= '2022-03-01' AND payment_date < '2022-05-01'

MISMATCH  film_actor             s10_nextjs: 4135   s10_nextjs_restored: 5462
MISMATCH  film_category          s10_nextjs: 1920   s10_nextjs_restored: 2367
MISMATCH  payment_p2022_03       s10_nextjs: 0   s10_nextjs_restored: 2713
MISMATCH  payment_p2022_04       s10_nextjs: 0   s10_nextjs_restored: 2547

film_actor: 4135 rows before, 5462 rows after, from s10_nextjs_2026-10-07_143844.dump in 0.27 s

SELECT count(*) FROM rental: 51805 in the clean container, 51805 in s10_nextjs -> OK
```

## Restoring a single table

`pg_restore --clean -t film_actor` would drop and recreate the table, and fails because the views `actor_info` and `film_list` depend on it. So `restore-table` empties the table with `TRUNCATE` and loads only its rows with `--data-only` (in one transaction). `payment` is partitioned: its rows live in the partitions (`payment_p2022_01`, ...), so `-t payment` restores nothing, and `TRUNCATE payment` would empty every partition. The script refuses a partitioned table and lists its partitions; restore the damaged ones by name. `verify` counts each partition separately, which is how it tells you which ones were hit.

## How this differs from your own environment

Several projects share the PostgreSQL server in this repository, so the scripts only touch databases whose names start with `s10_nextjs`, and the clean-container test uses a container named `s10-nextjs-pgtest` that is removed at the end. In your own environment you can rehearse the full disaster from the theory section: `docker compose down -v` deletes the volume with all the data, `docker compose up -d` starts an empty server, and you restore the roles (`psql < backups/roles_<stamp>.sql`) and then every database from its dump. Do not run `down -v` on a shared setup.

## Things to try

- Time `npm run restore` and write the number in `docs/runbook.md` as the expected time. That is your RTO for this database.
- Run `npm run backup`, make a change (add an actor in `psql`), then `npm run simulate-disaster` and restore. Which change is lost? That gap is your real RPO.
- Open the roles file in `backups/`. Which roles are there, and why does `pg_dump` alone not include them?
- Run `docker compose exec -T postgres pg_restore -l < backups/<your dump>.dump | head -40` to see the archive's table of contents: one entry per table, per table's data, per index and per constraint. `-t` selects entries from that list.
- Try `pg_restore --clean -t film_actor` yourself against `s10_nextjs_restored` and read the error about the dependent views.
