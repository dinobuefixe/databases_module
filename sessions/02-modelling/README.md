# Session 02: Modelling and normalisation

The tutorial from [session 02](../../README.md#session-02-modelling-er-diagrams-and-normalisation), written three times as independent projects.

The recipe spreadsheet from the tutorial, normalised into `author`, `recipe`, `ingredient` and `recipe_ingredient`, with `kcal_per_serving` stored on `recipe` as a deliberate denormalisation that is recalculated when the ingredients change.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | SQL schema file applied by a script, `psycopg` | 8000 |
| [django](django/) | Django models and a generated migration | 8001 |
| [nextjs](nextjs/) | Prisma schema and a generated migration | 3000 |

Compare how each one models the N:N relationship with its own column (`grams`), and where each one recalculates the stored calories inside a transaction.
