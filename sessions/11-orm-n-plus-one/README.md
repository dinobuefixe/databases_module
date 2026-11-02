# Session 11: The ORM and the N+1 problem

The tutorial from [session 11](../../README.md#session-11-orm-i-sqlalchemy), written three times as independent projects.

Pagila's `customer` and `rental` tables mapped in each ORM, a list of 20 customers with their rental counts loaded lazily (21 queries) and eagerly (2 queries), and the top 5 customers aggregated in the database. Every response says how many SQL statements it ran.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | SQLAlchemy 2, `selectinload`, `joinedload` | 8000 |
| [django](django/) | `prefetch_related`, `select_related` | 8001 |
| [nextjs](nextjs/) | a loop vs `include` and `_count` | 3000 |

Same problem, three ORMs: compare the names each one uses for eager loading and how each one lets you count queries.
