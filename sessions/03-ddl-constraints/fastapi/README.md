# Session 03 in FastAPI: DDL and constraints

The recipe model from session 02 as numbered SQL scripts, with every rule enforced by PostgreSQL. The API turns each constraint violation into a 409 or 422 response that names the constraint.

| File | What it shows |
|------|---------------|
| `sql/001_create_tables.sql` | The tutorial's DDL with named constraints: `CHECK`, `UNIQUE` (`email`, `ingredient.name`, `(author_id, title)`), foreign keys with `ON DELETE RESTRICT` and `CASCADE`. |
| `sql/002_seed.sql` | The spreadsheet rows from session 02. |
| `scripts/apply_sql.py` | Runs the numbered scripts in order, each in its own transaction, and records them in `applied_script` so each runs once. |
| `scripts/try_invalid.py` | The tutorial's invalid inserts, a duplicate `(author_id, title)`, deleting an author who has recipes (RESTRICT) and deleting a recipe (CASCADE removes its lines). Prints each error, then rolls everything back. |
| `app/main.py` | `POST /authors`, `POST /ingredients`, `POST /recipes`, `GET /recipes/{id}`, `DELETE /authors/{id}`, `DELETE /recipes/{id}`. Unique violations become 409, check and foreign key violations become 422, a RESTRICT refusal becomes 409. |

The Pydantic models check types only. That is deliberate: the requests reach the database so you can see it refuse them. In a real API you validate in the application as well, and the constraints stay as the last line of defence for every other client that writes to the database.

## Run it

From the root of the repository, start the engines and create this project's database:

```bash
docker compose up -d
./scripts/create-db.sh s03_fastapi
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.apply_sql
uv run python -m scripts.try_invalid
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

The tutorial applies the script with `psql` instead. On a new, empty database, this command from the repository root creates the same tables, without the seed and without recording the script in `applied_script`:

```bash
docker compose exec -T postgres psql -U postgres -d s03_fastapi -v ON_ERROR_STOP=1 \
  < sessions/03-ddl-constraints/fastapi/sql/001_create_tables.sql
```

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
# 201
curl -X POST localhost:8000/authors -H 'content-type: application/json' -d '{"name": "Marta", "email": "marta@example.com"}'
# 409, constraint author_email_unique
curl -X POST localhost:8000/authors -H 'content-type: application/json' -d '{"name": "Ana 2", "email": "ana@example.com"}'
# 422, constraint kcal_not_negative
curl -X POST localhost:8000/ingredients -H 'content-type: application/json' -d '{"name": "Sugar", "kcal_per_100g": -1}'
# 422, constraint recipe_author_fk
curl -X POST localhost:8000/recipes -H 'content-type: application/json' -d '{"author_id": 999, "title": "Soup", "servings": 4}'
# 409, constraint recipe_author_title_unique
curl -X POST localhost:8000/recipes -H 'content-type: application/json' -d '{"author_id": 1, "title": "Pancakes", "servings": 4}'
# 422, constraint grams_positive; the recipe is not saved either
curl -X POST localhost:8000/recipes -H 'content-type: application/json' \
  -d '{"author_id": 1, "title": "Milk pudding", "servings": 4, "ingredients": [{"ingredient_id": 2, "grams": 0}]}'
# 409, RESTRICT: Ana has recipes
curl -X DELETE localhost:8000/authors/1
# 200, CASCADE removes the recipe's ingredient lines
curl -X DELETE localhost:8000/recipes/2
```

To start again from an empty database, run `./scripts/create-db.sh s03_fastapi --reset` and `uv run python -m scripts.apply_sql`.

## Things to try

- Compare the constraint names in the errors with the names PostgreSQL generates when you leave them out (`author_email_key`, `ingredient_kcal_per_100g_check`, `recipe_author_id_fkey`). Which one would you rather read in a log?
- Look at the `RESTRICT` error: PostgreSQL reports SQLSTATE 23001 (`restrict_violation`). Change the constraint to the default `NO ACTION` and the error becomes 23503 (`foreign_key_violation`). Both refuse the delete; `NO ACTION` waits until the end of the statement to check, which matters for deferred constraints.
- Look at the `author_id` Marta received: 5, not 3. `try_invalid` used 3 and 4 inside a transaction that was rolled back, and identity values are never handed back.
- After `DELETE /recipes/2`, delete Rui with `DELETE /authors/2`. It works now because he has no recipes left.
- Add `sql/003_add_published_index.sql` with `CREATE INDEX ON recipe (published_at);` and run `uv run python -m scripts.apply_sql` again: only the new file runs.
- In `psql`, list the constraints of a table with `\d recipe`, or query them: `SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'recipe'::regclass;`
