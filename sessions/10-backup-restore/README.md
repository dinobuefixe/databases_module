# Session 10: Backup and restore

The tutorial from [session 10](../../README.md#session-10-backup-and-restore), written three times as independent projects.

The tutorial's backup and restore steps wrapped in each framework's tooling: a timestamped `pg_dump`, a timed restore into a new database, a single-table restore, a simulated disaster, a row-count verification that fails on any difference, a restore into a throwaway container, and an example runbook.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | Python scripts | 8000 |
| [django](django/) | Management commands | 8001 |
| [nextjs](nextjs/) | npm scripts | 3000 |

The commands underneath are the same `pg_dump` and `pg_restore` calls as the tutorial; only the entry point changes.
