# Session 03 in Next.js with Prisma: DDL and constraints

The recipe schema from the tutorial with every rule enforced by PostgreSQL. The API only checks types; when a request breaks a rule, the database refuses it and the API answers 409 or 422 with the constraint's name.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | `@unique`, `@@unique([authorId, title])`, `onDelete: Restrict` and `onDelete: Cascade`, all with explicit constraint names (`map:`). |
| `prisma/migrations/*_init/migration.sql` | The SQL Prisma generated, edited by hand to add the `CHECK` constraints and identity columns. |
| `src/lib/db-errors.ts` | Reads the SQLSTATE and constraint name from a Prisma error and maps it to 409 or 422. |
| `src/app/api/authors/route.ts` | `GET` and `POST /api/authors`. |
| `src/app/api/authors/[id]/route.ts` | `DELETE /api/authors/:id`, refused by `ON DELETE RESTRICT` while the author has recipes. |
| `src/app/api/ingredients/route.ts` | `GET` and `POST /api/ingredients`. |
| `src/app/api/recipes/route.ts` | `GET` and `POST /api/recipes` (recipe and lines in one statement). |
| `src/app/api/recipes/[id]/route.ts` | `DELETE /api/recipes/:id`; `ON DELETE CASCADE` removes the lines. |
| `scripts/try-invalid.ts` | Runs the tutorial's invalid inserts and the two `ON DELETE` cases, printing each outcome. |
| `scripts/seed.ts` | Two authors, three ingredients, two recipes. |

## What Prisma can and cannot express

| Tutorial rule | Where it lives here |
|---------------|---------------------|
| `PRIMARY KEY`, `NOT NULL`, `DEFAULT now()` | `schema.prisma` |
| `UNIQUE (email)`, `UNIQUE (name)`, `UNIQUE (author_id, title)` | `schema.prisma` (`@unique`, `@@unique`). Prisma creates them as unique indexes rather than `UNIQUE` constraints; PostgreSQL enforces both the same way and the error message is identical. |
| `REFERENCES ... ON DELETE RESTRICT / CASCADE` | `schema.prisma` (`onDelete:`) |
| `CHECK (...)` | Added by hand to the migration. Prisma's schema has no syntax for it. |
| `GENERATED ALWAYS AS IDENTITY` | Edited by hand in the migration. Prisma generates `SERIAL` for `@default(autoincrement())`. |

The workflow was: `npx prisma migrate dev --create-only --name init`, edit `migration.sql`, then `npx prisma migrate dev` to apply it. Running `npx prisma migrate dev --create-only` again produces an empty migration: Prisma does not compare `CHECK` constraints, so it neither adds nor drops them. That also means a later change to a `CHECK` must be written by hand in a new migration.

The `CHECK` constraints have names (`kcal_not_negative`, `servings_between_1_and_50`, `grams_positive`) so the error tells you which rule failed without reading the column list.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s03_nextjs
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npx prisma migrate dev
npm run seed
npm run try-invalid
npm run dev
```

Expected output of `npm run try-invalid` (abridged):

```
REJECTED  ingredient with negative calories
          kcal_not_negative (SQLSTATE 23514): new row for relation "ingredient" violates check constraint "kcal_not_negative"
REJECTED  recipe for an author that does not exist
          recipe_author_id_fkey (SQLSTATE 23503): ...
REJECTED  two authors with the same email
          author_email_key (SQLSTATE 23505): ...
...
REJECTED  delete an author who has recipes (RESTRICT)
          recipe_author_id_fkey (SQLSTATE 23001): ...
ACCEPTED  delete the recipe (CASCADE)
          recipe_ingredient lines for recipe 5: 1 before, 0 after
```

Try the API (after `npm run seed`):

```bash
curl -X POST localhost:3000/api/authors -H 'content-type: application/json' \
  -d '{"name": "Ana 2", "email": "ana@example.com"}'                         # 409 author_email_key
curl -X POST localhost:3000/api/ingredients -H 'content-type: application/json' \
  -d '{"name": "Sugar", "kcalPer100g": -1}'                                   # 422 kcal_not_negative
curl -X POST localhost:3000/api/recipes -H 'content-type: application/json' \
  -d '{"authorId": 999, "title": "Soup", "servings": 4}'                      # 422 recipe_author_id_fkey
curl -X POST localhost:3000/api/recipes -H 'content-type: application/json' \
  -d '{"authorId": 1, "title": "Pancakes", "servings": 2}'                    # 409 recipe_author_id_title_key
curl -X POST localhost:3000/api/recipes -H 'content-type: application/json' \
  -d '{"authorId": 1, "title": "Big pancakes", "servings": 60}'               # 422 servings_between_1_and_50
curl -X DELETE localhost:3000/api/authors/2                                   # 409 recipe_author_id_fkey
curl -X DELETE localhost:3000/api/recipes/2                                   # 200, linesRemovedByCascade: 1
curl -X DELETE localhost:3000/api/authors/2                                   # 204, Rui has no recipes now
```

## Things to try

- Open `psql` (`docker compose exec postgres psql -U postgres -d s03_nextjs`) and run `\d recipe`. Compare the output with the `CREATE TABLE` in the tutorial: the check constraint, the unique index and both foreign keys are listed.
- Run the tutorial's invalid inserts in `psql` and compare the messages with the JSON the API returns.
- Insert a recipe with an explicit id: `INSERT INTO recipe (recipe_id, author_id, title, servings) VALUES (100, 1, 'Toast', 1);`. `GENERATED ALWAYS` refuses it; with `SERIAL` it would be accepted and the sequence would later collide with it.
- Notice that a failed insert still uses up an identity value: after a few rejected requests, the next author does not get the next number. Identity values are not meant to have no gaps.
- Change a `CHECK` in `schema.prisma`? You cannot. Write a new migration with `npx prisma migrate dev --create-only --name servings_up_to_100`, put `ALTER TABLE recipe DROP CONSTRAINT servings_between_1_and_50, ADD CONSTRAINT ...` in it, and apply it.
