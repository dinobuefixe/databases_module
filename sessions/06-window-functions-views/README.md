# Session 06: Window functions and views

The tutorial from [session 06](../../README.md#session-06-queries-ii-window-functions-and-views), written three times as independent projects.

The tutorial on a copy of Pagila: the longest films per rating with `DENSE_RANK`, a running total of payments, gaps between rentals with `LAG`, and the `daily_rentals` materialised view with a concurrent refresh.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | SQL with `psycopg` | 8000 |
| [django](django/) | `Window`, `DenseRank`, `Lag`; the view in a `RunSQL` migration | 8001 |
| [nextjs](nextjs/) | `$queryRaw`; the view in a hand-written migration | 3000 |

Django can express window functions and filter on them; Prisma cannot, so its version uses SQL.
