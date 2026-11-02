# Session 14: Aggregation pipelines and reports

The tutorial from [session 14](../../README.md#session-14-mongodb-ii-aggregation-pipelines-and-reports), written three times as independent projects.

A loader builds the `films` and `customers` collections from Pagila, the tutorial's three pipelines run behind endpoints, a monthly report is frozen from PostgreSQL with a deterministic `_id` (201 the first time, 409 after), and this project's MongoDB database is backed up and restored.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `pymongo` | 8000 |
| [django](django/) | `pymongo` | 8001 |
| [nextjs](nextjs/) | `mongodb` driver | 3000 |

The pipelines are the same JSON in all three languages. The interesting difference is how each one handles the duplicate key error that keeps the report frozen.
