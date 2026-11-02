# Session 01: Database engines

The tutorial from [session 01](../../README.md#session-01-database-engines-and-diagnosis), written three times. Each project connects to PostgreSQL, MongoDB and Redis, pings them, and writes and reads the same message in each one.

| Project | PostgreSQL | MongoDB | Redis | Port |
|---------|------------|---------|-------|------|
| [fastapi](fastapi/) | `psycopg`, plain SQL | `pymongo` | `redis` | 8000 |
| [django](django/) | Django ORM and migrations | `pymongo` | `redis` | 8001 |
| [nextjs](nextjs/) | Prisma 7 | `mongodb` driver | `redis` | 3000 |

Compare how each one creates the `hello` table: a `CREATE TABLE` string in FastAPI, a model and a generated migration in Django and in Prisma.
