# Session 17: Integration and disaster day

The tutorial from [session 17](../../README.md#session-17-project-integration-and-disaster-day), written three times as independent projects.

Each project is a small API that uses the three engines together, built from earlier sessions: account withdrawals in PostgreSQL (session 08), rentals that keep the derived `customer:{id}:films` sets in Redis up to date (session 16), and a frozen monthly report in MongoDB (session 14). On top of it:

- `tests/concurrency/` runs against the running API and checks the business rules under concurrent requests;
- `scripts/backup.sh`, `scripts/restore.sh <postgres|mongo|redis>` and `scripts/verify.sh`. Redis is restored by rebuilding it from PostgreSQL, because its data is derived;
- `docs/runbook-restore.md`, the runbook the scripts follow.

| Project | Concurrency tests | Port |
|---------|-------------------|------|
| [fastapi](fastapi/) | pytest | 8000 |
| [django](django/) | pytest | 8001 |
| [nextjs](nextjs/) | `node --test` with `tsx` | 3000 |

The rehearsal in each README deletes only that project's own databases. On disaster day the trainer deletes a whole Docker volume; each runbook includes the `docker volume rm` steps for your own environment.
