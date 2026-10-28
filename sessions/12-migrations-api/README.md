# Session 12: Migrations, transactions and an API

The tutorial from [session 12](../../README.md#session-12-orm-ii-migrations-transactions-and-api), written three times as independent projects.

Migrations on an existing database: a baseline for Pagila's `customer` table, a `balance` column, and the tutorial's three-step `tier` migration with a working downgrade. A charge endpoint locks the row and returns 409 when the balance is too low.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | Alembic | 8000 |
| [django](django/) | Django migrations | 8001 |
| [nextjs](nextjs/) | Prisma Migrate, baseline with `migrate diff` and `resolve` | 3000 |

Bringing an existing database under migrations is different in each tool. Read how each project builds its baseline.
