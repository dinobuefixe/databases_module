# Session 04: CRUD, upsert and bulk data

The tutorial from [session 04](../../README.md#session-04-crud-upsert-and-bulk-data), written three times as independent projects.

The tutorial on a copy of Pagila: filtered reads, `INSERT ... RETURNING`, an update that rolls back when the row count is not the one expected, an upsert into `film_views`, and 100,000 rows loaded with `COPY`, a batch insert and one `INSERT` per row, with timings.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `psycopg`: `COPY`, `executemany` | 8000 |
| [django](django/) | ORM, `bulk_create`, `COPY` through the cursor | 8001 |
| [nextjs](nextjs/) | Prisma, `createMany`, `COPY` with `pg-copy-streams` | 3000 |

Run the bulk load in each one and compare the timings. In all three, one `INSERT` per row is by far the slowest.
