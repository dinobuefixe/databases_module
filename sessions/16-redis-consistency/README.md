# Session 16: Source of truth, rebuild and persistence

The tutorial from [session 16](../../README.md#session-16-redis-ii-source-of-truth-rebuild-and-persistence), written three times as independent projects.

The `customer:{id}:films` sets derived from PostgreSQL, rebuilt into a temporary key and renamed (one query per customer, then one query and one pipeline), a verification that exits non-zero on a mismatch, the server's persistence settings, and a username change with `WATCH` and with Lua.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `redis-py`, SQL with `psycopg` | 8000 |
| [django](django/) | `redis-py`, Django ORM | 8001 |
| [nextjs](nextjs/) | `redis` (node-redis), Prisma | 3000 |

The tutorial uses `FLUSHALL`. These projects use `FLUSHDB` because the three frameworks share one Redis server on different logical databases; in your own environment `FLUSHALL` is fine.
