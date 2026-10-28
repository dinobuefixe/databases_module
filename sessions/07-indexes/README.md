# Session 07: Indexes and optimisation

The tutorial from [session 07](../../README.md#session-07-indexes-and-optimisation), written three times as independent projects.

The tutorial's 2,000,000-row `big_rental` table, `EXPLAIN (ANALYZE, BUFFERS)` before and after a composite, a partial and an expression index, and the extra cost those indexes add to every insert.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | Indexes declared with SQLAlchemy `Index` | 8000 |
| [django](django/) | `Meta.indexes` with `condition` and expressions | 8001 |
| [nextjs](nextjs/) | `@@index`, partial index as a preview feature, expression index in SQL | 3000 |

Each README lists which index types its tool can declare and which ones need raw SQL.
