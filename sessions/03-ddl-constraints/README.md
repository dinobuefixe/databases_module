# Session 03: DDL and constraints

The tutorial from [session 03](../../README.md#session-03-sql-ddl-data-types-and-constraints), written three times as independent projects.

The recipe schema with every rule from the tutorial enforced by PostgreSQL: `CHECK`, `UNIQUE` (including the composite one), and foreign keys with `ON DELETE RESTRICT` and `CASCADE`. Each API turns a violation into a 409 or 422 that names the constraint, and a `try_invalid` script runs the tutorial's invalid inserts.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | Numbered `.sql` scripts, `psycopg` | 8000 |
| [django](django/) | `Meta.constraints` and database-level `on_delete` | 8001 |
| [nextjs](nextjs/) | `onDelete` in the schema, `CHECK` added by hand to a migration | 3000 |

This session shows where each tool stops: Prisma's schema cannot declare `CHECK` constraints, and Django 6.1 has no database-level restrict action. Each README explains its workaround.
