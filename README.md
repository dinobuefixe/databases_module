
> [!IMPORTANT]
> The content of this file was co-authored with Claude Code. It helped me write this content with given restricted guidelines. 
> Please open a PR or reach out to me if you find any error or missing piece or simply for any type of feedback.

# Databases Module

Module 11 of the Web Programming course (PW 25/27). 19 sessions of 3 hours, 57 hours in total.

You will design, build, secure, optimise and recover the databases of a web application that uses three engines, each for the job it does best:

- **PostgreSQL** (relational) for domain data that must never be lost or contradict itself
- **MongoDB** (documents) for reports that are read often and change shape from case to case
- **Redis** (in-memory key-value) for rankings, counters and temporary reservations that change many times per second

The exercises use the Pagila sample database (a DVD rental shop) so that every student works on the same data. The group project uses all three engines in a different scenario per group.

## Getting started

1. Fork this repository to your own GitHub account and clone your fork.
2. Install Docker Desktop (or Docker Engine with the Compose plugin on Linux).
3. Copy `.env.example` to `.env`. Never commit `.env`.
4. Start the engines:

   ```bash
   docker compose up -d
   ```

5. Check that all three services are `healthy`:

   ```bash
   docker compose ps
   ```

6. Load the Pagila sample database (needed from session 04):

   ```bash
   ./scripts/load-pagila.sh
   ```

From session 04 onwards you will also need Python 3.12+ and [uv](https://docs.astral.sh/uv/). Every Python project in this module declares its dependencies in `pyproject.toml`: `uv add <package>` adds one, `uv sync` installs them into `.venv/`, and `uv run <command>` runs a command inside that environment.

## Example code for each session

`sessions/NN-topic/` holds the session's tutorial written three times, as three independent projects: `fastapi/`, `django/` and `nextjs/` (Next.js with Prisma). Pick the framework you know best, then compare it with the other two. Each project has a README with the steps to run it.

Each project uses its own database so the three never interfere. Create it from the repository root before running the project, as the project's README says:

```bash
./scripts/create-db.sh s04_fastapi --pagila   # a copy of Pagila
./scripts/create-db.sh s02_django             # an empty database
```

The Next.js projects use Prisma for PostgreSQL and the official `mongodb` driver for MongoDB, because Prisma 7 does not support MongoDB.

These projects show the tutorial, not the exercise. Your exercise answers still go in `exercises/`.

## Submitting exercises and challenges

Sessions 01 to 16 each have one individual exercise and one challenge, and sessions 17 to 19 have one individual challenge. Work in your fork and put each one in its own folder, using the folder given in the session:

```
exercises/
  01-diagnosis/
    exercise/
      README.md
      ...
    challenge/
      README.md
      ...
```

- The `README.md` in each folder is the entry point. It lists every file you submit, the exact commands to run them from the repository root, and the evidence the brief asks for.
- Paste query results and command output as text in fenced code blocks. Use a screenshot only when the brief asks for one.
- Every SQL file must run with `psql -v ON_ERROR_STOP=1` on a fresh database created as the brief says, for example `./scripts/create-db.sh ex04 --pagila`. Work on that copy, never on `pagila` itself, so a mistake in one exercise does not break the next one.
- Every Python deliverable is a uv project with its own `pyproject.toml` and runs with `uv run`. The connection URLs it needs are in `.env.example`.
- The briefs use Python (psycopg, SQLAlchemy, Alembic, FastAPI, pymongo, redis-py). You may answer with the stack of one of the session example projects instead (Django ORM and migrations, or Next.js with Prisma and the official MongoDB and Redis drivers), as long as every requirement of the brief is met and the README says how to run it.
- Never commit `.env`, dumps or `.venv/`.
- Commit and push before the end of session 19.

Each brief has the same parts: **Goal**, **Starting point** (what you need before you start, with the commands to create it), **Tasks**, **Deliverables** (the files to submit) and **Done when** (how the answer is checked). When a brief builds on an earlier exercise, the starting point also gives what you need to do it without that exercise.

Challenges for sessions 01 to 07 are mandatory. Challenges from session 08 onwards are optional.

Each exercise (sessions 01 to 16) and each mandatory challenge (sessions 01 to 07) is marked 0 (not submitted), 1 (incomplete or with relevant errors) or 2 (complete and correct). Optional challenges are not marked.

Sessions 17 to 19 are dedicated to the group project, which is defined in its own brief.

## Sessions

- [Session 01: Database engines and diagnosis](#session-01-database-engines-and-diagnosis)
- [Session 02: Modelling, ER diagrams and normalisation](#session-02-modelling-er-diagrams-and-normalisation)
- [Session 03: SQL DDL, data types and constraints](#session-03-sql-ddl-data-types-and-constraints)
- [Session 04: CRUD, upsert and bulk data](#session-04-crud-upsert-and-bulk-data)
- [Session 05: Queries I, joins, aggregation, subqueries and CTEs](#session-05-queries-i-joins-aggregation-subqueries-and-ctes)
- [Session 06: Queries II, window functions and views](#session-06-queries-ii-window-functions-and-views)
- [Session 07: Indexes and optimisation](#session-07-indexes-and-optimisation)
- [Session 08: Transactions and concurrency](#session-08-transactions-and-concurrency)
- [Session 09: Security](#session-09-security)
- [Session 10: Backup and restore](#session-10-backup-and-restore)
- [Session 11: ORM I, SQLAlchemy](#session-11-orm-i-sqlalchemy)
- [Session 12: ORM II, migrations, transactions and API](#session-12-orm-ii-migrations-transactions-and-api)
- [Session 13: MongoDB I, documents, CRUD and validation](#session-13-mongodb-i-documents-crud-and-validation)
- [Session 14: MongoDB II, aggregation pipelines and reports](#session-14-mongodb-ii-aggregation-pipelines-and-reports)
- [Session 15: Redis I, data structures and patterns](#session-15-redis-i-data-structures-and-patterns)
- [Session 16: Redis II, source of truth, rebuild and persistence](#session-16-redis-ii-source-of-truth-rebuild-and-persistence)
- [Session 17: Project integration and disaster day](#session-17-project-integration-and-disaster-day)
- [Session 18: Cross-group review and documentation](#session-18-cross-group-review-and-documentation)
- [Session 19: Delivery and technical discussion](#session-19-delivery-and-technical-discussion)

---

## Session 01: Database engines and diagnosis

### Theory

A JSON file can store data, but it guarantees almost nothing. If two processes write to it at the same time, one write is lost. If the process crashes halfway through a write, the file may be corrupt. Finding one record means reading the whole file. Nothing stops a price from being stored as `"abc"`.

A database engine adds four guarantees on top of storage: persistence (data survives a crash), querying (you ask for what you need without reading everything), integrity (rules the data must follow) and concurrency (many clients read and write safely at once).

Engines differ in how they model data:

- **Relational (PostgreSQL)**: tables with fixed columns, linked by keys. Strong integrity rules and transactions across many tables. Good for orders, payments, bank statements, anything where two records must never contradict each other.
- **Documents (MongoDB)**: JSON-like documents grouped in collections. A document can nest lists and sub-documents, and documents in the same collection can have different shapes. Good for catalogues with variable attributes and for reports read as a whole.
- **Key-value in memory (Redis)**: values (strings, lists, sets, sorted sets, hashes) stored under keys, kept in RAM. Very fast, with built-in expiry. Good for rankings, session data, counters and caches.

Relational engines offer ACID transactions: Atomicity (all or nothing), Consistency (rules hold before and after), Isolation (concurrent transactions do not see each other's half-finished work) and Durability (a committed change survives a crash). Engines that relax these guarantees gain speed or scale, and the application has to deal with what is lost.

A real application often uses more than one engine. When it does, each piece of data needs one **source of truth**: the engine whose copy wins if they disagree. Session 16 covers this in depth.

### Tutorial

Start the module environment and connect to each engine from the command line. Usernames and passwords are in your `.env`.

```bash
docker compose up -d
docker compose ps
```

PostgreSQL:

```bash
docker compose exec postgres psql -U postgres
```

```sql
CREATE TABLE hello (id integer PRIMARY KEY, msg text NOT NULL);
INSERT INTO hello VALUES (1, 'first row');
SELECT * FROM hello;
```

MongoDB:

```bash
docker compose exec mongo mongosh -u root -p --authenticationDatabase admin
```

```js
use sandbox
db.hello.insertOne({ msg: "first document", tags: ["a", "b"] })
db.hello.find()
```

Redis:

```bash
docker compose exec redis redis-cli
```

```
AUTH <password from .env>
SET hello "first key"
GET hello
```

Now stop everything and start it again. The data is still there because each service stores its files in a named Docker volume:

```bash
docker compose down
docker compose up -d
```

`docker compose down -v` deletes the volumes, and the data with them.

To classify a use case, ask: must this data never be lost or contradicted? Is it read as a whole and does its shape vary? Does it change many times per second and can it be rebuilt or expire? Try it on: bank statement, shopping basket, catalogue with variable attributes, recently viewed products, login session, price history, orders, page view counter.

### Exercise (individual)

Folder: `exercises/01-diagnosis/exercise/`

**Goal.** Diagnose the problems of a small shop that keeps its data in a JSON file, and decide which engine each kind of data belongs in.

**Starting point.** The module environment running (`docker compose up -d`). Save the following content as `shop.json` in your exercise folder, exactly as shown, so that line numbers match:

```json
{
  "customers": [
    {"id": 1, "name": "Ana Silva", "email": "ana@example.com", "city": "Porto"},
    {"id": 2, "name": "Rui Costa", "email": "rui@example.com", "city": "Lisboa"}
  ],
  "orders": [
    {"id": 1, "customer_id": 1, "customer_name": "Ana Silva", "customer_email": "ana@example.com",
     "items": "Keyboard x1; Mouse x2", "total": "59.90", "date": "07/10/2026"},
    {"id": 2, "customer_id": 3, "customer_name": "Marta Reis", "customer_email": "marta@example",
     "items": "Monitor x1", "total": "abc", "date": "2026-10-08"},
    {"id": 2, "customer_id": 1, "customer_name": "Ana Silva", "customer_email": "ana.silva@example.com",
     "items": "Mouse x-1", "total": 12.5, "date": "08/10/2026"}
  ],
  "products": [
    {"name": "Keyboard", "price": 29.90, "stock": 3},
    {"name": "Mouse", "price": "15", "stock": -2}
  ]
}
```

The shop's application reads the whole file, changes it in memory and writes the whole file back on every request.

**Tasks.**

1. Take a screenshot of `docker compose ps` with the three engines `healthy`.
2. Describe the data model of `shop.json`: the entities, their fields and the relationships between them.
3. Find at least 5 concrete problems in `shop.json`. For each one give the line number, the kind of problem (for example duplicated data, missing integrity rule, wrong type, a list stored in a single field, inconsistent format) and what can go wrong because of it.
4. Explain what happens to this design with 100,000 orders (finding the orders of one customer, adding one order) and when two requests add an order at the same time.
5. Say which engine (PostgreSQL, MongoDB or Redis) you would use for each of these and why: customers, orders, products, the last 10 products a customer viewed, the number of times each product page was opened today.

**Deliverables.**

- `README.md` with the screenshot and the answers to tasks 2 to 5.
- `shop.json`.

**Done when.** The screenshot shows the three services `healthy`, at least 5 problems of at least 3 different kinds are identified by line, and every engine choice in task 5 has a reason based on the theory of this session.

### Challenge (mandatory)

Folder: `exercises/01-diagnosis/challenge/`

**Goal.** Show with numbers why a database engine handles concurrent writes and a JSON file does not.

**Starting point.** Create an empty database and a uv project:

```bash
./scripts/create-db.sh ch01
uv init --bare
uv add "psycopg[binary]"
```

Use this table in `ch01` database (create if it doesn't exist):

```sql
CREATE TABLE record (worker integer NOT NULL, n integer NOT NULL);
```

**Tasks.**

1. `json_race.py`: create `records.json` containing `[]`. Start 10 processes with `multiprocessing`. Each process appends 1,000 records of the form `{"worker": <process number>, "n": <0 to 999>}`, one at a time: read the whole file, append one record, write the whole file back. Do not use any file lock. A process may read a half-written file that is not valid JSON: catch that error, count it as a failed write and carry on. At the end, print how many records the file holds and how many writes failed.
2. `pg_race.py`: start 10 processes, each with its own connection, each inserting the same 1,000 records into `record` with one `INSERT` per record. At the end, print `SELECT count(*) FROM record`.
3. Run each script 3 times (empty the file and the table before each run).

**Deliverables.**

- `json_race.py`, `pg_race.py`, `pyproject.toml`.
- `README.md` with the commands to run both scripts, the count of each of the 3 runs of each script, and an explanation of a few sentences of why the numbers differ.

**Done when.** The JSON count is below 10,000 and changes between runs, the PostgreSQL count is exactly 10,000 in every run, and the explanation names the cause (lost updates from concurrent read-modify-write, and how the engine avoids them).

---

## Session 02: Modelling, ER diagrams and normalisation

### Theory

A data model starts from requirements written in plain language. Nouns usually become **entities** (tables), verbs become **relationships**, and business rules become **constraints**. "A reader borrows copies of a book" gives you `reader`, `copy`, `book` and a `loan` relationship.

An **entity-relationship (ER) diagram** shows entities, their attributes and how they relate. Crow's foot notation marks **cardinality** (how many) and **optionality** (whether the relationship is required):

- 1:1, for example a user and their profile
- 1:N, for example a customer and their orders
- N:N, for example books and authors. A relational database cannot store N:N directly, so you add an **association table** (`book_author`) with a foreign key to each side. If the relationship has its own data (the date a student enrolled in a course), that data lives in the association table.

A UML class diagram shows similar information with a focus on objects and behaviour. Use ER for the database and UML when you are designing application classes.

Every table needs a primary key. A **natural key** comes from the domain (an ISBN, a tax number). A **surrogate key** is an artificial identifier (`id` generated by the database). Surrogate keys are stable when domain values change; keep natural keys as `UNIQUE` constraints.

**Normalisation** removes redundancy so that each fact is stored once:

- **1NF**: every column holds a single value. No lists in a cell, no `phone1`, `phone2`, `phone3`.
- **2NF**: 1NF, and every non-key column depends on the whole primary key, not just part of it (relevant for composite keys).
- **3NF**: 2NF, and no non-key column depends on another non-key column. If `postcode` determines `city`, `city` belongs in another table.

Redundant data causes three anomalies: **insertion** (you cannot record a product until someone orders it), **update** (you change a customer's address in one row and forget the others) and **deletion** (removing the last order deletes the only record of the customer).

**Denormalisation** is sometimes the right call, as long as it is deliberate and written down. There are two usual reasons. Speed: a blog post stores its comment count so the listing page does not count comments for every post, at the cost of updating the count on every new comment. History: a parcel stores the address it was sent to, which must not change when the customer later moves house.

### Tutorial

Take this spreadsheet from a recipe website:

| recipe_id | title | author | author_email | ingredient | kcal_per_100g | grams |
|-----------|-------|--------|--------------|------------|---------------|-------|
| 1 | Pancakes | Ana | ana@example.com | Flour | 364 | 200 |
| 1 | Pancakes | Ana | ana@example.com | Milk | 42 | 300 |
| 2 | Omelette | Rui | rui@example.com | Egg | 155 | 120 |

Problems: Ana's email is stored twice, and so would the calories of flour be in every recipe that uses it (update anomaly); you cannot add an ingredient no recipe uses yet (insertion anomaly); deleting recipe 2 loses Rui (deletion anomaly).

Step by step:

1. Identify entities: author, recipe, ingredient. Recipes and ingredients are N:N, and the relationship has its own data (grams), so it becomes an association table `recipe_ingredient`.
2. Move each fact to the table it depends on: email depends on the author, calories on the ingredient, the title on the recipe, the grams on the recipe-ingredient pair.
3. Decide on denormalisation. The listing page shows calories per serving for every recipe. You could store `kcal_per_serving` on `recipe` so the page does not sum ingredients for each row, and recalculate it whenever the ingredients change. Write the decision down either way.

```mermaid
erDiagram
    AUTHOR ||--o{ RECIPE : writes
    RECIPE ||--|{ RECIPE_INGREDIENT : uses
    INGREDIENT ||--o{ RECIPE_INGREDIENT : "appears in"

    AUTHOR {
        int author_id PK
        text name
        text email UK
    }
    RECIPE {
        int recipe_id PK
        int author_id FK
        text title
        int servings
    }
    INGREDIENT {
        int ingredient_id PK
        text name UK
        numeric kcal_per_100g
    }
    RECIPE_INGREDIENT {
        int recipe_id PK, FK
        int ingredient_id PK, FK
        numeric grams
    }
```

GitHub renders Mermaid inside Markdown, so the diagram can live in your README and be versioned with the code.

### Exercise (individual)

Folder: `exercises/02-modelling/exercise/`

**Goal.** Turn written requirements into an ER diagram and a set of tables in 3NF.

**Starting point.** The requirements of a municipal library:

- A reader has a unique card number, a name, a unique email, a phone number, an address and a registration date.
- A book has a unique ISBN-13, a title, a publication year, exactly one publisher and one or more authors. An author can write many books. For each book, the order of its authors matters (first author, second author, ...).
- A publisher has a unique name and a country.
- The library owns one or more copies of each book. A copy has a unique barcode, an acquisition date and a condition: `new`, `good`, `worn` or `damaged`.
- A reader borrows a copy. A loan records the reader, the copy, the loan date, the due date (14 days after the loan date) and the return date, which stays empty until the copy is returned. A copy can be in at most one open loan at a time. A reader can have at most 5 open loans.
- A reader can reserve a book (not a specific copy) when no copy of it is available. Reservations for the same book are served in the order they were made. A reservation is `active`, `fulfilled` or `cancelled`.
- A late return creates a fine of 0.50 per day late. A fine belongs to exactly one loan and records its amount and the date it was paid, which stays empty until it is paid.

**Tasks.**

1. Draw an ER diagram in Mermaid (`erDiagram`, as in the tutorial) with every entity, its attributes, primary keys, foreign keys and the cardinality of every relationship.
2. List the tables in 3NF. For each table give its columns, its primary key, its foreign keys and its `UNIQUE` columns.
3. List the business rules from the requirements that a table structure alone cannot enforce (for example "at most 5 open loans") and say where you would enforce each one: a constraint, a trigger or the application.
4. Describe one denormalisation you would make and why, or explain why you would make none.

**Deliverables.** `model.md` with the diagram and the answers to tasks 2 to 4. Check on GitHub that the diagram renders.

**Done when.** Every requirement above appears in the model, the N:N relationship between books and authors has an association table that keeps the author order, the tables are in 3NF, and the diagram renders on GitHub.

### Challenge (mandatory)

Folder: `exercises/02-modelling/challenge/`

**Goal.** Extend a model with history and check it against a stricter normal form.

**Starting point.** The requirements of the exercise above. You can start from your own model.

**Tasks.**

1. The library opens three branches. Each copy belongs to one home branch, can be transferred to another branch, and can be returned at any branch. Extend the model so that it records where each copy is at any moment and the full history of its transfers (from, to, date and who authorised it).
2. Write two queries in plain language that the new model must answer, for example "where is copy X now?" and "which copies left branch Y last month?", and show which tables answer each one.
3. Find a table in your model that is in 3NF but not in BCNF (Boyce-Codd normal form), or show that none exists. Explain the difference between the two forms with an example.

**Deliverables.** `model.md` with the extended Mermaid diagram, the new and changed tables, and the answers to tasks 2 and 3.

**Done when.** The current location of a copy can be found without reading its whole history (or the README explains why reading the history is acceptable), every transfer is kept, and the BCNF answer includes the functional dependencies that justify it.

---

## Session 03: SQL DDL, data types and constraints

### Theory

DDL (Data Definition Language) is the part of SQL that creates and changes structure: `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`. A **schema** is a namespace that groups tables; PostgreSQL creates `public` by default.

Choosing data types is part of modelling:

- `integer` for most counts and IDs; `bigint` when a table can pass 2 billion rows.
- `numeric(10,2)` for money. Never `float` or `real`: they cannot store 0.10 exactly, and rounding errors add up.
- `text` for strings. `varchar(n)` only when the limit is a real business rule.
- `timestamptz` for moments in time. It stores UTC and converts on display. Plain `timestamp` has no time zone and causes bugs when servers or users are in different zones.
- `boolean`, `date`, `uuid` where they fit.
- An enum type or a reference table for a fixed list of values. A reference table is easier to change and can hold extra data (a label, an order).
- `jsonb` for data whose shape really varies and is not queried relationally. It is not a way to skip modelling.

Use **identity columns** for surrogate keys: `integer GENERATED ALWAYS AS IDENTITY`.

**Constraints** are domain rules enforced by the database, whatever application writes to it:

- `PRIMARY KEY`: unique and not null.
- `FOREIGN KEY`: the referenced row must exist.
- `UNIQUE`: no duplicates, including across several columns (`UNIQUE (author_id, title)`: one author cannot publish two recipes with the same title).
- `CHECK`: a condition each row must meet (`CHECK (quantity > 0)`).
- `NOT NULL` and `DEFAULT`.

Each foreign key needs an `ON DELETE` behaviour chosen from the domain:

- `RESTRICT` (or the default `NO ACTION`): refuse to delete a parent that has children. Use it when deleting would lose history (an author with published recipes).
- `CASCADE`: delete the children too. Use it when the children have no meaning without the parent (the ingredient list of a recipe).
- `SET NULL`: keep the child and clear the link. Use it when the relationship is optional (a task assigned to an employee who leaves).

Keep the schema in numbered scripts (`001_create_tables.sql`, `002_add_indexes.sql`) so that anyone can rebuild it in order. In session 12 these become Alembic migrations.

### Tutorial

Implement the recipe model from session 02:

```sql
CREATE TABLE author (
    author_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       text NOT NULL,
    email      text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ingredient (
    ingredient_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name          text NOT NULL UNIQUE,
    kcal_per_100g numeric(6,1) NOT NULL CHECK (kcal_per_100g >= 0)
);

CREATE TABLE recipe (
    recipe_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- RESTRICT: an author with published recipes cannot be deleted by accident
    author_id    integer NOT NULL REFERENCES author ON DELETE RESTRICT,
    title        text NOT NULL,
    servings     integer NOT NULL CHECK (servings BETWEEN 1 AND 50),
    published_at timestamptz,
    UNIQUE (author_id, title)
);

CREATE TABLE recipe_ingredient (
    -- CASCADE: the ingredient list means nothing without its recipe
    recipe_id     integer NOT NULL REFERENCES recipe ON DELETE CASCADE,
    ingredient_id integer NOT NULL REFERENCES ingredient ON DELETE RESTRICT,
    grams         numeric(7,1) NOT NULL CHECK (grams > 0),
    PRIMARY KEY (recipe_id, ingredient_id)
);
```

Now try to break the rules and read the error each time:

```sql
INSERT INTO ingredient (name, kcal_per_100g) VALUES ('Sugar', -1);
-- ERROR: new row for relation "ingredient" violates check constraint "ingredient_kcal_per_100g_check"

INSERT INTO recipe (author_id, title, servings) VALUES (999, 'Soup', 4);
-- ERROR: insert or update on table "recipe" violates foreign key constraint "recipe_author_id_fkey"

INSERT INTO author (name, email) VALUES ('Ana', 'ana@example.com'), ('Ana 2', 'ana@example.com');
-- ERROR: duplicate key value violates unique constraint "author_email_key"
```

Name your constraints (`CONSTRAINT kcal_not_negative CHECK (kcal_per_100g >= 0)`) when you want clearer error messages in the application.

Save the script as `001_create_tables.sql` and run it on an empty database:

```bash
docker compose exec -T postgres createdb -U postgres recipes
docker compose exec -T postgres psql -U postgres -d recipes -v ON_ERROR_STOP=1 < 001_create_tables.sql
```

### Exercise (individual)

Folder: `exercises/03-ddl/exercise/`

**Goal.** Implement the municipal library in PostgreSQL with data types and constraints that enforce its rules.

**Starting point.** The library requirements in the exercise of session 02. You may implement your own model from that exercise or a corrected version of it. Create an empty database:

```bash
./scripts/create-db.sh ex03
```

**Tables** Implement tables ``,``,``,``,``

**Tasks.**

1. Write `schema.sql`, which creates every table of the library. Use identity columns for surrogate keys, `numeric` for money and `timestamptz` or `date` for dates. Include at least:
   - one `CHECK` (for example the condition of a copy, or a due date after the loan date);
   - one composite `UNIQUE`;
   - one `ON DELETE RESTRICT` and one `ON DELETE CASCADE`, each justified in a comment.
2. Write `invalid.sql` with 5 `INSERT` or `DELETE` statements that must fail, each rejected by a different constraint. Above each statement, add a comment with the name of the constraint that rejects it.

Run the files in this order to check them:

```bash
docker compose exec -T postgres psql -U postgres -d ex03 -v ON_ERROR_STOP=1 < exercises/03-ddl/exercise/schema.sql
docker compose exec -T postgres psql -U postgres -d ex03 < exercises/03-ddl/exercise/invalid.sql
```

**Deliverables.**

- `schema.sql`, `invalid.sql`.
- `README.md` with the output of running `invalid.sql`.

**Done when.** `schema.sql` run on an empty database without errors, and each of the 5 statements in `invalid.sql` fails with the error of the constraint named in its comment.

### Challenge (mandatory)

Folder: `exercises/03-ddl/challenge/`

**Goal.** Make the database itself reject invalid ISBNs.

**Starting point.** An empty database (`./scripts/create-db.sh ch03`). You may add the domain to your library schema; if you do not, use this table:

```sql
CREATE TABLE book (
    book_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn    isbn13 NOT NULL UNIQUE,
    title   text NOT NULL
);
```

An ISBN-13 has 13 digits. Hyphens may appear between digits, never at the start or the end and never two in a row. The last digit is a check digit: multiply the first 12 digits alternately by 1 and 3, add the results, and the check digit is `(10 - sum % 10) % 10`.

**Tasks.**

1. Write an `IMMUTABLE` SQL function `is_valid_isbn13(text) RETURNS boolean` that checks the format and the check digit.
2. Create `DOMAIN isbn13 AS text CHECK (is_valid_isbn13(VALUE))` and use it in the `book` table.
3. Prove that these values are accepted: `978-0-306-40615-7`, `9781402894626`, `978-3-16-148410-0`. Prove that these are rejected: `978-0-306-40615-8` (wrong check digit), `978-0-306-4061` (too short), `-9780306406157` (leading hyphen), `978--0306406157` (two hyphens in a row).
4. Explain why the function must be `IMMUTABLE`.

**Deliverables.**

- `isbn.sql` with the function, the domain, the table and the 7 test inserts.
- `README.md` with the output of `isbn.sql` and the explanation of task 4.

**Done when.** The 3 valid values are inserted, the 4 invalid ones fail with a domain check error, and the explanation is correct.

---

## Session 04: CRUD, upsert and bulk data

### Theory

CRUD covers the four basic operations: Create (`INSERT`), Read (`SELECT`), Update (`UPDATE`) and Delete (`DELETE`).

`SELECT` filters with `WHERE` using `=`, `<>`, `<`, `>`, `LIKE` (case-sensitive pattern), `ILIKE` (case-insensitive), `IN (...)`, `BETWEEN` and `IS NULL`. Note that `= NULL` never matches anything; use `IS NULL`. `ORDER BY` sorts, `DISTINCT` removes duplicates, and `LIMIT`/`OFFSET` paginate.

`UPDATE` and `DELETE` without a correct `WHERE` change every row in the table. Two habits prevent this: run a `SELECT` with the same `WHERE` first and check the row count, and run the change inside a transaction so you can `ROLLBACK` if the count is wrong.

`RETURNING` makes `INSERT`, `UPDATE` and `DELETE` return the affected rows, which saves a second query to find a generated ID.

An **upsert** inserts a row, or updates it if it already exists, in one atomic statement: `INSERT ... ON CONFLICT (key) DO UPDATE` or `DO NOTHING`. It needs a `UNIQUE` or primary key constraint on the conflict columns.

Testing with ten rows hides problems that appear with a million. Generate test data in volume, and make it **reproducible** with a fixed random seed so that everyone gets the same data and results can be compared. For large loads, `COPY` is much faster than individual `INSERT` statements because it streams rows in one command.

### Tutorial

Load Pagila (the script is in this repository):

```bash
./scripts/load-pagila.sh
docker compose exec postgres psql -U postgres -d pagila
```

Read:

```sql
SELECT title, length, rating
FROM film
WHERE rating = 'R' AND title ILIKE '%love%'
ORDER BY length DESC
LIMIT 10;
```

Insert and get the generated key back:

```sql
INSERT INTO actor (first_name, last_name)
VALUES ('ADA', 'LOVELACE')
RETURNING actor_id, last_update;
```

Safe update:

```sql
BEGIN;
SELECT count(*) FROM film WHERE rating = 'NC-17' AND rental_rate < 1;  -- expect N rows
UPDATE film SET rental_rate = 1.99
WHERE rating = 'NC-17' AND rental_rate < 1
RETURNING film_id, title, rental_rate;
-- the count matches N? COMMIT. Otherwise ROLLBACK.
COMMIT;
```

Upsert into a table with a primary key:

```sql
CREATE TABLE film_views (
    film_id integer PRIMARY KEY REFERENCES film,
    views   integer NOT NULL DEFAULT 0
);

INSERT INTO film_views (film_id, views) VALUES (1, 1)
ON CONFLICT (film_id) DO UPDATE SET views = film_views.views + 1
RETURNING *;
```

Run the upsert twice and watch `views` go from 1 to 2.

Bulk data in SQL, reproducible with `setseed`:

```sql
SELECT setseed(0.42);

CREATE TABLE reading AS
SELECT g AS reading_id,
       now() - random() * interval '365 days' AS taken_at,
       round((random() * 100)::numeric, 2)    AS value
FROM generate_series(1, 1000000) AS g;
```

Bulk data in Python with Faker and `COPY` (in a uv project: `uv add faker "psycopg[binary]"`, then `uv run python seed.py`):

```python
import os
import psycopg
from faker import Faker

Faker.seed(42)
fake = Faker("en_GB")

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor().copy("COPY person (name, email, city) FROM STDIN") as copy:
        for _ in range(500_000):
            copy.write_row((fake.name(), fake.unique.email(), fake.city()))
```

Time the same load with one `INSERT` per row to see the difference.

### Exercise (individual)

Folder: `exercises/04-crud/exercise/`

**Goal.** Read, insert, update and delete data safely, and use upsert.

**Starting point.** A fresh copy of Pagila:

```bash
./scripts/create-db.sh ex04 --pagila --reset
```

The expected results below assume the operations run in this order on a fresh copy.

**Tasks.** Write one statement (or one short transaction) per operation:

1. Films rated `PG-13` and longer than 120 minutes, sorted by title. Expected: 118 rows, from `APOLLO TEEN` to `WRONG BEHAVIOR`.
2. Actors whose last name contains `son`, in any case. Expected: 9 rows.
3. Rentals that have not been returned yet. Expected: 241 rows.
4. The distinct values of `rental_duration` in `film`, in ascending order. Expected: 5 rows, `3` to `7`.
5. The third page of films ordered by title, 10 films per page. Expected: 10 rows, from `AMERICAN CIRCUS` to `ANYTHING SAVANNAH`.
6. The number of rentals made in January 2026, written twice: with `rental_date BETWEEN '2026-01-01' AND '2026-01-31'`, and with `rental_date >= '2026-01-01' AND rental_date < '2026-02-01'`. Expected: 746 and 781. Explain in a comment why they differ and which one is correct.
7. Insert the actor `ADA LOVELACE` and get the generated `actor_id` back with `RETURNING`. Expected: 1 row with `actor_id` 201.
8. In a transaction, raise the `rental_rate` of films rated `NC-17` and shorter than 60 minutes by 0.50. First run a `SELECT count(*)` with the same `WHERE`, then the `UPDATE ... RETURNING film_id, title, rental_rate`, then `COMMIT`. Expected: 21 rows in both.
9. Create the table below, then write an upsert that adds one award to actor 1 (insert with 1, or add 1 if the row exists). Run it twice. Expected: `awards` is 2.

   ```sql
   CREATE TABLE actor_award (
       actor_id integer PRIMARY KEY REFERENCES actor,
       awards   integer NOT NULL DEFAULT 0
   );
   ```

10. Insert actor 2 with 5 awards using `ON CONFLICT DO NOTHING`, and run it twice. Expected: the first run inserts 1 row, the second inserts 0 rows.
11. Insert 3 test payments in one statement: `customer_id` 1, `staff_id` 2, `rental_id` 76, `amount` 0.01, `payment_date` `'2026-07-30 12:00+00'`. Return their `payment_id` with `RETURNING`. Expected: 3 rows.
12. Delete the 3 test payments. First run a `SELECT count(*)` with the `WHERE` you will use, then the `DELETE ... RETURNING`, inside a transaction. Expected: 3 rows in both.

**Deliverables.**

- `queries.sql` with the 12 operations, numbered with a comment (`-- 1.`, `-- 2.`, ...).
- `README.md` with the output of each operation (for long results, the row count and the first and last rows).

**Done when.** `queries.sql` runs from top to bottom on a fresh copy with `ON_ERROR_STOP=1` and every result matches the expected one.

### Challenge (mandatory)

Folder: `exercises/04-crud/challenge/`

**Goal.** Generate a large, valid and reproducible data set quickly.

**Starting point.** Two fresh copies of Pagila and a uv project:

```bash
./scripts/create-db.sh ch04_a --pagila --reset
./scripts/create-db.sh ch04_b --pagila --reset
uv init --bare
uv add faker "psycopg[binary]"
```

**Tasks.**

1. Write `seed.py`, which adds 1,000,000 rows to `rental` using `COPY`. The database name is a command-line argument.
   - Use explicit `rental_id` values from 100,001 to 1,100,000, so that both runs produce the same keys. After the load, move the sequence past the last ID with `setval`.
   - Every `inventory_id`, `customer_id` and `staff_id` must exist in Pagila.
   - `rental_date` is between `2022-01-01` and `2026-07-31`; `return_date` is either `NULL` or later than `rental_date`.
   - Respect the existing unique index on `(rental_date, inventory_id, customer_id)`.
   - Overlapping rentals of the same copy are allowed in this challenge.
   - Use a fixed random seed.
2. Run it on `ch04_a` and on `ch04_b` and time each run.
3. Prove that both databases have identical new rows by comparing this checksum on both:

   ```sql
   SELECT md5(string_agg(concat_ws('|', rental_id, rental_date, inventory_id, customer_id, return_date, staff_id), ',' ORDER BY rental_id))
   FROM rental WHERE rental_id > 100000;
   ```

4. Make the script idempotent: running it a second time on `ch04_a` must not add or change any row. Prove it with the row count and the checksum before and after.

**Deliverables.**

- `seed.py`, `pyproject.toml`.
- `README.md` with the run commands, the measured times, both checksums and the idempotency proof.

**Done when.** Each load adds exactly 1,000,000 valid rows, takes under 30 seconds on your machine (report the time), the two checksums are equal, and the second run on the same database changes nothing.

---

## Session 05: Queries I, joins, aggregation, subqueries and CTEs

### Theory

A **join** combines rows from two tables where a condition holds.

- `INNER JOIN` keeps only rows with a match on both sides.
- `LEFT JOIN` keeps every row from the left table; columns from the right are `NULL` where there is no match.
- A **self join** joins a table to itself, for example to find pairs of rows that share something.

Joining along a 1:N relationship repeats the "1" side once per match. If you then `SUM` a column from the "1" side, you count it several times. Aggregate before joining, or check row counts as you add each join.

An **anti-join** finds rows with no match: `LEFT JOIN ... WHERE right.id IS NULL`, or `WHERE NOT EXISTS (...)`. `NOT EXISTS` is usually clearer. Avoid `NOT IN (subquery)` when the subquery can return `NULL`: it then returns no rows at all.

**Aggregation** collapses groups of rows into one: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` with `GROUP BY`. `WHERE` filters rows before grouping; `HAVING` filters groups after. `COUNT(*)` counts rows; `COUNT(column)` counts non-null values in that column, which matters after a `LEFT JOIN`.

A **subquery** is a query inside another one: in `WHERE` (`price > (SELECT avg(price) FROM product)`), in `FROM` as a derived table, or **correlated**, referring to the outer row and evaluated per row. `EXISTS` checks whether a subquery returns any row.

A **CTE** (`WITH name AS (...)`) names an intermediate result so you can build a complex query in readable steps. Since PostgreSQL 12, simple CTEs are inlined, so they cost nothing extra.

The method for a business question: write down what one result row is (a customer? a month per category?), find the tables that hold the data, join them one at a time while checking row counts, then aggregate and filter.

### Tutorial

"How many rentals has each staff member handled, per store?"

```sql
SELECT s.store_id, st.first_name, st.last_name, count(*) AS rentals
FROM rental r
JOIN staff st ON st.staff_id = r.staff_id
JOIN store s  ON s.store_id  = st.store_id
GROUP BY s.store_id, st.staff_id
ORDER BY s.store_id, rentals DESC;
```

"Which customers rented more than 40 films?" (`HAVING`)

```sql
SELECT c.customer_id, c.first_name, c.last_name, count(*) AS rentals
FROM customer c
JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
HAVING count(*) > 40
ORDER BY rentals DESC;
```

"How many rentals has each customer made, including customers with none?" (`LEFT JOIN`, `COUNT(*)` vs `COUNT(column)`)

```sql
SELECT c.customer_id, c.first_name, c.last_name,
       count(r.rental_id) AS rentals,
       count(*)           AS joined_rows
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY rentals, c.customer_id;
```

999 rows, one per customer. Customers 647 and 978 have no rentals. The `LEFT JOIN` gives each of them one row with `NULL` in every `rental` column, so `count(r.rental_id)` is 0 and `count(*)` is 1. With `JOIN` instead of `LEFT JOIN` those two customers disappear and you get 997 rows.

"Which films have no copy in any store?" (anti-join)

```sql
SELECT f.film_id, f.title
FROM film f
WHERE NOT EXISTS (
    SELECT 1 FROM inventory i WHERE i.film_id = f.film_id
);
```

"Which customers have never rented a film?" (the same anti-join written with `LEFT JOIN ... IS NULL`)

```sql
SELECT c.customer_id, c.first_name, c.last_name
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
WHERE r.rental_id IS NULL
ORDER BY c.customer_id;
```

Two rows, customers 647 and 978. Test `IS NULL` on a column of the right table that can never be `NULL` in a real row, such as its primary key. Otherwise a row that exists but has a `NULL` in that column looks like a missing match.

"Which customers share their first and last name with another customer?" (self join, to look for duplicate accounts)

```sql
SELECT c1.customer_id, c2.customer_id AS other_customer_id, c1.first_name, c1.last_name
FROM customer c1
JOIN customer c2
  ON  c2.first_name  = c1.first_name
  AND c2.last_name   = c1.last_name
  AND c2.customer_id > c1.customer_id
ORDER BY c1.last_name, c1.first_name, c1.customer_id, other_customer_id;
```

The same table appears twice under two aliases. 20 pairs. `c2.customer_id > c1.customer_id` leaves out each customer paired with itself and lists each pair once: with `<>` you get 40 rows, and with no condition on the id 1,039. A name shared by three customers, such as JAMES BROWN, gives three pairs.

"Which films are longer than the average film?" (subquery in `WHERE`)

```sql
SELECT f.film_id, f.title, f.length
FROM film f
WHERE f.length > (SELECT avg(length) FROM film)
ORDER BY f.length DESC, f.film_id;
```

489 films; the average is 115.27 minutes. The subquery does not refer to the outer query, so PostgreSQL runs it once. `EXPLAIN` shows it as an `InitPlan`.

"Which films are longer than the average film with the same rating?" (correlated subquery)

```sql
SELECT f.film_id, f.title, f.rating, f.length
FROM film f
WHERE f.length > (
    SELECT avg(f2.length) FROM film f2 WHERE f2.rating = f.rating
)
ORDER BY f.rating, f.length DESC, f.film_id;
```

497 films. `f2.rating = f.rating` refers to the current row of the outer query, so the subquery is evaluated for each film, against the average of its rating: from 111.1 minutes for G to 120.4 for PG-13. `EXPLAIN` shows a `SubPlan`.

"How many rentals has each customer made, and how much have they paid?" A first attempt that joins both tables to `customer`:

```sql
SELECT c.customer_id, count(r.rental_id) AS rentals, sum(p.amount) AS paid
FROM customer c
JOIN rental  r ON r.customer_id = c.customer_id
JOIN payment p ON p.customer_id = c.customer_id
WHERE c.customer_id = 1
GROUP BY c.customer_id;
```

Customer 1 has 66 rentals and 65 payments that add up to 217.35. This query says 4,290 rentals and 14,345.10 paid. Both joins are 1:N from `customer`, so every rental is paired with every payment of the same customer: 66 × 65 = 4,290 rows, and each payment is summed 66 times. Aggregate each table first in a subquery in `FROM` (a derived table), then join results that have one row per customer:

```sql
SELECT c.customer_id, c.first_name, c.last_name,
       coalesce(r.rentals, 0) AS rentals,
       coalesce(p.paid, 0)    AS paid
FROM customer c
LEFT JOIN (
    SELECT customer_id, count(*) AS rentals FROM rental GROUP BY customer_id
) r ON r.customer_id = c.customer_id
LEFT JOIN (
    SELECT customer_id, sum(amount) AS paid FROM payment GROUP BY customer_id
) p ON p.customer_id = c.customer_id
ORDER BY c.customer_id;
```

999 rows, and customer 1 shows 66 and 217.35. `coalesce` turns the `NULL` of the two customers with no rentals and no payments into 0.

"Which customers spent more than the average customer?" (CTE in steps)

```sql
WITH spend AS (
    SELECT customer_id, sum(amount) AS total
    FROM payment
    GROUP BY customer_id
),
average AS (
    SELECT avg(total) AS avg_total FROM spend
)
SELECT c.first_name, c.last_name, s.total
FROM spend s
JOIN customer c ON c.customer_id = s.customer_id
CROSS JOIN average a
WHERE s.total > a.avg_total
ORDER BY s.total DESC;
```

### Exercise (individual)

Folder: `exercises/05-queries/exercise/`

**Goal.** Answer business questions with joins, aggregation, subqueries and CTEs.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ex05 --pagila --reset`). In this version of Pagila a film can belong to more than one category; when a question is per category, a film counts in each of its categories.

**Tasks.** Write one query per question. Window functions are not allowed in this exercise (they are the topic of session 06).

1. The number of films per category, including categories with no films, most films first, then by category name. Expected: 16 rows; the first two are `Drama` and `Music`, with 152 films each.
2. Revenue per category per month in 2025, by `payment_date`. Expected: 192 rows; `Action` in January 2025 has 314.94.
3. Films that have never been rented, including films with no copy in any store. Expected: 42 rows.
4. Customers who have rented films of all 5 ratings. Expected: 908 rows.
5. Pairs of actors who appeared together in more than 3 films, each pair listed once, with the number of films (self join). Expected: 143 rows.
6. Countries with more than 20 customers, with the number of customers and the total they paid, most customers first. Expected: 7 rows; the first is `Mexico` with 430 customers.
7. Customers who paid more in total than the average customer of their own country. A customer with no payments counts as 0. Expected: 449 rows.
8. The longest films of each rating, including ties, using a subquery. Expected: 14 rows.
9. Customers with no rental on or after `2026-04-01`. Expected: 49 rows.
10. For each category, the average number of days a film stays out (`return_date - rental_date`, returned rentals only), rounded to 2 decimals, highest first. Expected: 16 rows; the first is `Sci-Fi` with 5.30.

**Deliverables.**

- `queries.sql` with the 10 queries, each preceded by a comment with its number and the question.
- `README.md` with the row count and the first 5 rows of each result.

**Done when.** Every query runs on a fresh copy and returns the expected number of rows and values.

### Challenge (mandatory)

Folder: `exercises/05-queries/challenge/`

**Goal.** Walk a graph stored in tables with a recursive CTE.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ch05 --pagila --reset`). Two actors are connected when they appeared together in at least 3 films. The distance between two actors is the smallest number of connections between them ("degrees of separation").

**Tasks.**

1. Write a CTE `edge(actor_id, other_actor_id)` with every connected pair, in both directions.
2. Write a query with `WITH RECURSIVE` that, starting from actor 1, lists every actor reachable within 3 degrees with columns `actor_id`, `first_name`, `last_name`, `distance` (the shortest one), ordered by distance and `actor_id`. Actor 1 is not in the result. The query must stop on its own and must never revisit an actor on the same path (keep the path in an array).
3. Change the query to return the shortest path from actor 1 to actor 200 as the list of actor names, or an empty result if there is no path within 5 degrees.

**Deliverables.**

- `degrees.sql` with the queries of tasks 2 and 3.
- `README.md` with the number of actors at each distance, the result of task 3, and an explanation of how the query avoids running forever.

**Done when.** Task 2 returns data where you can identify relationships and you verify that there's no issues.

---

## Session 06: Queries II, window functions and views

### Theory

A **window function** computes a value over a set of rows related to the current row, without collapsing them. `GROUP BY` returns one row per group; a window function keeps every row and adds a column.

```sql
function() OVER (PARTITION BY ... ORDER BY ... [frame])
```

- `PARTITION BY` splits the rows into groups. The function restarts in each partition.
- `ORDER BY` inside `OVER` sets the order within the partition.

Ranking functions differ in how they treat ties:

| Scores | `ROW_NUMBER` | `RANK` | `DENSE_RANK` |
|--------|--------------|--------|--------------|
| 100 | 1 | 1 | 1 |
| 100 | 2 | 1 | 1 |
| 90 | 3 | 3 | 2 |

`ROW_NUMBER` gives arbitrary order among ties, so it is the wrong choice when ties must share a position.

**Top N per group**: rank inside a partition, then filter in an outer query or CTE. You cannot use a window function in `WHERE` directly.

**Running totals** use `SUM(x) OVER (ORDER BY date)`. `LAG(x)` and `LEAD(x)` read the value from the previous or next row, useful for "change since last month".

A **view** is a saved query used like a table. It holds no data and runs the query every time. A **materialised view** stores the result; it is fast to read but stale until you refresh it. `REFRESH MATERIALIZED VIEW CONCURRENTLY` lets readers keep reading during the refresh, and requires a unique index on the materialised view.

### Tutorial

The two longest films per rating, with ties:

```sql
WITH ranked AS (
    SELECT title, rating, length,
           DENSE_RANK() OVER (PARTITION BY rating ORDER BY length DESC) AS pos
    FROM film
)
SELECT * FROM ranked WHERE pos <= 2 ORDER BY rating, pos;
```

Running total of each customer's payments:

```sql
SELECT customer_id, payment_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY payment_date) AS running_total
FROM payment
WHERE customer_id IN (1, 2)
ORDER BY customer_id, payment_date;
```

Time between consecutive rentals of the same customer:

```sql
SELECT customer_id, rental_date,
       rental_date - LAG(rental_date) OVER (PARTITION BY customer_id ORDER BY rental_date) AS gap
FROM rental
WHERE customer_id = 1;
```

Materialised view of rentals per day:

```sql
CREATE MATERIALIZED VIEW daily_rentals AS
SELECT rental_date::date AS day, count(*) AS rentals
FROM rental
GROUP BY 1;

CREATE UNIQUE INDEX ON daily_rentals (day);

REFRESH MATERIALIZED VIEW CONCURRENTLY daily_rentals;
```

### Exercise (individual)

Folder: `exercises/06-window/exercise/`

**Goal.** Rank, accumulate and compare rows with window functions, and keep a report in a materialised view.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ex06 --pagila --reset`).

**Tasks.**

1. The 3 most rented films of each category, by number of rentals. Films tied on the same number share a position, and every film in positions 1 to 3 is listed. Expected: 56 rows.
2. Revenue per day in July 2026, with the running total for the month. Columns: `day`, `revenue`, `running_total`. Expected: 28 rows; the last running total is 2409.88.
3. Revenue per month for the whole data set, with the change from the previous month in value and in percentage (1 decimal). Expected: 55 rows; July 2026 has 2409.88, the previous month 2105.73, a change of 304.15 and 14.4%.
4. Each customer's position in the ranking of their store by total paid. Customers with no payments count as 0, and tied customers share a position. Expected: 999 rows; customer 468 is first in store 1 (344.06) and customer 526 is first in store 2 (358.12).
5. The top 5 customers of each store by total paid. Expected: 10 rows.

**Deliverables.**

- `queries.sql` with the 6 tasks, each preceded by a comment with its number.
- `README.md` with the row count and the first 5 rows of each result, and the output of the steps of task 6.

**Done when.** Every query runs on a fresh copy and returns the expected rows and values, and the materialised view changes only after the refresh.

### Challenge (mandatory)

Folder: `exercises/06-window/challenge/`

**Goal.** Solve a "gaps and islands" problem with window functions.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ch06 --pagila --reset`). An island is a run of consecutive calendar months in which a customer rented at least one film. In Pagila, March and April 2022 have no rentals at all.

**Tasks.**

1. For each customer, find their longest island: `customer_id`, `first_month`, `last_month`, `months`. When a customer has two islands of the same length, keep the earliest.
2. Return the 10 customers with the longest islands, longest first, ties broken by `customer_id`.
3. Use window functions and set operations only: no procedural code, no recursive CTE.

**Deliverables.**

- `islands.sql` with the query.
- `README.md` with the 10 rows of the result and an explanation of the technique you used to group consecutive months.

**Done when.** The first row is customer 70 with 19 months, from 2023-06 to 2024-12, and the tenth row is customer 556 with 16 months.

---

## Session 07: Indexes and optimisation

### Theory

PostgreSQL stores tables in 8 KB pages. To answer a query it can:

- **Seq scan**: read every page of the table. Fine for small tables or when most rows match.
- **Index scan**: walk an index to find matching rows, then fetch each row from the table.
- **Index only scan**: answer from the index alone, when it contains every column the query needs.
- **Bitmap scan**: collect matching row locations from the index, sort them by page, then read each page once. Used for medium selectivity.

The **planner** picks a plan using statistics about the data (row counts, value distribution), gathered by `ANALYZE` (autovacuum runs it for you). Bad statistics lead to bad plans.

`EXPLAIN` shows the chosen plan and the estimated cost. `EXPLAIN (ANALYZE, BUFFERS)` runs the query and adds real times, real row counts and how many pages came from memory or disk. A large gap between estimated and actual rows is a sign of stale statistics.

A **B-tree** index (the default) supports `=`, `<`, `>`, `BETWEEN`, `ORDER BY` and prefix `LIKE 'abc%'`.

- **Composite index** on `(a, b)`: works for filters on `a`, or on `a` and `b`, but not on `b` alone. Put the column used for equality first and the range or sort column second.
- **Partial index**: `WHERE return_date IS NULL` indexes only the rows you query, so it is smaller and faster.
- **Expression index**: `ON customer (lower(email))` lets `WHERE lower(email) = ...` use an index.

PostgreSQL does **not** create indexes on foreign key columns automatically. Joins and `ON DELETE` checks on unindexed foreign keys get slow.

An index will not help when:

- the filter matches a large share of the table (low selectivity, for example `active = true` on 95% of rows);
- the query wraps the column in a function the index does not cover (`WHERE date(created_at) = ...`);
- the pattern starts with a wildcard (`LIKE '%text'`).

Indexes cost disk space and slow down every `INSERT`, `UPDATE` and `DELETE`, because each index must be updated too. Create an index for a measured problem, not in case.

`pg_stat_statements` records the total time spent on each query shape, so you can find which queries are worth optimising.

### Tutorial

Create a large table to see real differences:

```sql
SELECT setseed(0.1);
CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, 2000000) AS g;
VACUUM ANALYZE big_rental;
```

`ANALYZE` gives the planner fresh statistics. `VACUUM` also records which pages hold only rows every transaction can see, which autovacuum would otherwise do a little later. The challenge at the end of this session asks why that matters for some plans.

Before:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM big_rental WHERE customer_id = 42 ORDER BY rented_at DESC LIMIT 10;
```

Look for `Seq Scan`, the `actual time` and `Buffers: shared read`.

Add a composite index that matches the filter and the sort, then run the same `EXPLAIN` again:

```sql
CREATE INDEX big_rental_customer_rented ON big_rental (customer_id, rented_at DESC);
```

Partial index for rentals not yet returned:

```sql
CREATE INDEX big_rental_open ON big_rental (rented_at) WHERE returned_at IS NULL;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days';
```

Measure the write cost:

```sql
\timing on
INSERT INTO big_rental SELECT g, 1, now(), NULL FROM generate_series(2000001, 2100000) g;
```

Compare the time with and without the indexes. Record each case as: query, plan before, index, plan after, times, one sentence explaining the difference.

### Exercise (individual)

Folder: `exercises/07-indexes/exercise/`

**Goal.** Read query plans, create indexes that a measured query needs, and recognise when an index cannot help.

**Starting point.** An empty database (`./scripts/create-db.sh ex07 --reset`) with the `big_rental` table of the tutorial, created by this script (`setup.sql`):

```sql
SELECT setseed(0.1);
CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, 2000000) AS g;
VACUUM ANALYZE big_rental;
```

The table has no indexes at the start. Analyse these 5 queries:

```sql
-- Q1
SELECT count(*) FROM big_rental WHERE customer_id = 42 AND returned_at IS NULL;

-- Q2
SELECT * FROM big_rental WHERE rented_at >= now() - interval '1 day' ORDER BY rented_at;

-- Q3
SELECT * FROM big_rental WHERE rented_at::date = current_date - 10;

-- Q4
SELECT customer_id, count(*) FROM big_rental WHERE returned_at IS NOT NULL GROUP BY customer_id;

-- Q5
SELECT * FROM big_rental
WHERE customer_id IN (7, 42, 99) AND rented_at >= now() - interval '30 days'
ORDER BY rented_at DESC;
```

**Tasks.**

1. For each query, explain in one or two sentences what it returns.
2. Run `EXPLAIN (ANALYZE, BUFFERS)` on each query without indexes. Run it 3 times and keep the median execution time.
3. For each query, create the index you think it needs and run the same `EXPLAIN` again. Name the plan node used before and after (`Seq Scan`, `Index Scan`, `Index Only Scan`, `Bitmap Heap Scan`).
4. Not every query can be made faster by an index as it is written. When an index does not help, prove it with the plans and explain why. If rewriting the query lets an index help, show the rewritten query and its plan.
5. Measure the write cost: time `INSERT INTO big_rental SELECT g, 1, now(), NULL FROM generate_series(2000001, 2100000) g;` on a table with no indexes and on a table with all your indexes (recreate the table with `setup.sql` between runs).

**Deliverables.**

- `setup.sql`, and `indexes.sql` with every `CREATE INDEX` you kept.
- `README.md` with, for each query: what it does, the key lines of the plan before, the index created (or "none"), the key lines of the plan after, the median times before and after, and one or two sentences explaining the difference. Then the two insert times and an explanation of the difference.

**Done when.** Every query has plans before and after, every index is justified by a measured improvement, and every query that an index cannot speed up is explained with its plan.

### Challenge (mandatory)

Folder: `exercises/07-indexes/challenge/`

**Goal.** Compare `OFFSET` pagination with keyset pagination, and connect index only scans to `VACUUM`.

**Starting point.** The `big_rental` table of the exercise above, created with its `setup.sql` in a database of its own (`./scripts/create-db.sh ch07 --reset`). Pages are 20 rows of the whole table ordered by `rented_at DESC, id DESC`. Page 5,000 starts after 99,980 rows.

**Tasks.**

1. Create an index that matches the sort order.
2. Read page 5,000 with `ORDER BY rented_at DESC, id DESC OFFSET 99980 LIMIT 20` and record its plan and time with `EXPLAIN (ANALYZE, BUFFERS)`.
3. Read the same page with keyset pagination. Store the last row of page 4,999 in psql variables, then use them:

   ```sql
   SELECT rented_at AS last_rented_at, id AS last_id
   FROM big_rental ORDER BY rented_at DESC, id DESC OFFSET 99979 LIMIT 1 \gset

   SELECT id, rented_at, customer_id FROM big_rental
   WHERE (rented_at, id) < (:'last_rented_at', :last_id)
   ORDER BY rented_at DESC, id DESC LIMIT 20;
   ```

   Show that both queries return the same 20 rows, and compare the plans and times.
4. Recreate the index with `INCLUDE (customer_id)` so that the keyset query becomes an `Index Only Scan`.
5. Run `UPDATE big_rental SET customer_id = customer_id WHERE id % 50 = 0;`, run the keyset query again and read the `Heap Fetches` line. Then run `VACUUM big_rental;` and run it once more.

**Deliverables.**

- `pagination.sql` with every statement in order.
- `README.md` with the plans and times of tasks 2, 3 and 5, and an explanation of why `OFFSET` gets slower as the page number grows, and of what `VACUUM` changes in the visibility map that makes `Heap Fetches` drop.

**Done when.** The two methods return the same rows, the keyset query does not depend on the page number, the plan of task 4 is an `Index Only Scan`, and `Heap Fetches` is above 0 after the update and 0 after `VACUUM`.

---

## Session 08: Transactions and concurrency

### Theory

A **transaction** groups several statements so they succeed or fail together: `BEGIN`, then your statements, then `COMMIT` (keep everything) or `ROLLBACK` (undo everything). Without `BEGIN`, PostgreSQL runs in **autocommit**: each statement is its own transaction.

ACID in practice:

- **Atomicity**: a transfer debits one account and credits another, or does neither.
- **Consistency**: constraints hold at the end of every transaction.
- **Isolation**: concurrent transactions do not see each other's uncommitted changes.
- **Durability**: after `COMMIT` returns, the change survives a crash.

**Isolation levels** set how much concurrent transactions can affect each other:

- `READ COMMITTED` (PostgreSQL default): each statement sees data committed before it started. Two reads in the same transaction can return different values.
- `REPEATABLE READ`: the whole transaction sees one snapshot. If it tries to update a row another transaction changed, it fails with a serialisation error.
- `SERIALIZABLE`: the result is as if transactions ran one after another. Conflicting transactions fail and must be retried by the application.

**Write skew** is an anomaly that `REPEATABLE READ` does not prevent: two transactions read the same rows, each updates a different row, and together they break a rule that neither broke alone. Example: two doctors on call each check "is someone else on call?", both see yes, and both go off call. `SERIALIZABLE` detects it.

A **lost update** happens when two transactions read the same value, compute a new one, and both write: the second write overwrites the first. Under `READ COMMITTED` this is a real risk with read-then-write code.

Ways to protect a rule, from simplest to heaviest:

1. **Constraint**: `UNIQUE`, `CHECK`, or `EXCLUDE` (with `btree_gist` for ranges). The database refuses the second write. This is the last line of defence and should exist even when you also use the options below.
2. **Atomic conditional update**: `UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10`. Read and write happen in one statement; check the affected row count.
3. **Row lock**: `SELECT ... FOR UPDATE` locks the rows until the transaction ends; other transactions trying to lock them wait. `FOR UPDATE SKIP LOCKED` skips locked rows instead of waiting, which is how you build a job queue.
4. **Stricter isolation level** with retries.

A **deadlock** happens when transaction A holds lock 1 and waits for lock 2, while B holds lock 2 and waits for lock 1. PostgreSQL detects it after about a second and aborts one of them. Prevent it by always locking rows in the same order (for example by ascending ID), and retry the aborted transaction.

Concurrency bugs rarely show up when you test by hand. Write an automated test that fires many requests at the same time and checks the rule still holds. `pgbench` with a custom script is another way to generate concurrent load.

### Tutorial

Open two `psql` sessions side by side.

```sql
CREATE TABLE account (id int PRIMARY KEY, balance numeric NOT NULL CHECK (balance >= 0));
INSERT INTO account VALUES (1, 100);
```

Reproduce a lost update:

| Session A | Session B |
|-----------|-----------|
| `BEGIN;` | |
| `SELECT balance FROM account WHERE id = 1;` → 100 | |
| | `BEGIN;` |
| | `SELECT balance FROM account WHERE id = 1;` → 100 |
| `UPDATE account SET balance = 90 WHERE id = 1;` | |
| `COMMIT;` | |
| | `UPDATE account SET balance = 80 WHERE id = 1;` |
| | `COMMIT;` |

The final balance is 80. It should be 70.

Fix 1, atomic update (each session runs this instead of reading first):

```sql
UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10;
```

Fix 2, row lock:

```sql
BEGIN;
SELECT balance FROM account WHERE id = 1 FOR UPDATE;  -- B waits here until A commits
UPDATE account SET balance = 90 WHERE id = 1;
COMMIT;
```

Provoke a deadlock with two rows: A locks row 1 then row 2, B locks row 2 then row 1. Read the `ERROR: deadlock detected` message and the detail lines.

Test concurrency from Python:

```python
import os
from concurrent.futures import ThreadPoolExecutor
import psycopg

DSN = os.environ["DATABASE_URL"]

def withdraw(_):
    with psycopg.connect(DSN) as conn:
        cur = conn.execute(
            "UPDATE account SET balance = balance - 10 WHERE id = %s AND balance >= 10",
            (1,),
        )
        return cur.rowcount == 1

# account 1 starts with a balance of 100
with ThreadPoolExecutor(max_workers=50) as pool:
    results = list(pool.map(withdraw, range(50)))

assert sum(results) == 10, f"{sum(results)} withdrawals succeeded"
```

Rewrite `withdraw` as read-then-write without a lock and watch the assertion fail.

### Exercise (individual)

Folder: `exercises/08-transactions/exercise/`

**Goal.** Reproduce lost updates, deadlocks and write skew, and fix each one.

**Starting point.** A fresh copy of Pagila and a uv project:

```bash
./scripts/create-db.sh ex08 --pagila --reset
uv init --bare
uv add "psycopg[binary]"
```

Run this once in `ex08`. It adds a balance to every customer and brings store 1 from 6 to 20 active staff members:

```sql
ALTER TABLE customer ADD COLUMN balance numeric(10,2) NOT NULL DEFAULT 100 CHECK (balance >= 0);

INSERT INTO staff (first_name, last_name, address_id, store_id, username)
SELECT 'Temp', 'Staff ' || g, 1, 1, 'temp' || g
FROM generate_series(1, 14) AS g;
```

**Tasks.**

1. Lost update. In two `psql` sessions, each session withdraws 10 from customer 1 by reading the balance with `SELECT` and then writing the new value with `UPDATE ... SET balance = <value read - 10>`. Interleave the steps as in the tutorial so that the final balance is 90 instead of 80. Reset the balance to 100 afterwards.
2. Fix the lost update in two ways, repeating the same interleaving each time: an atomic `UPDATE ... SET balance = balance - 10 WHERE ... AND balance >= 10`, and `SELECT ... FOR UPDATE` before the update. Show that the final balance is 80 with both fixes.
3. Deadlock. In two sessions, session A updates customer 1 and then customer 2, and session B updates customer 2 and then customer 1, interleaved so that each waits for the other. Copy the full `ERROR: deadlock detected` message and explain each of its lines. Explain how to prevent it.
4. Write skew. The rule: every store keeps at least one active staff member. Write `write_skew.py`, which starts 20 threads, one per active staff member of store 1, each with its own connection. Each thread runs one transaction: count the active staff of store 1; if the count is above 1, set its own member to `active = false`; commit. Use a `threading.Barrier(20)` between the count and the update so that every thread reads before any thread writes.
   1. Run it under `READ COMMITTED` and show the number of active members of store 1 afterwards.
   2. Reset with `UPDATE staff SET active = true WHERE store_id = 1;`.
   3. Run it under `SERIALIZABLE`, retrying a transaction that fails with a serialisation error (SQLSTATE `40001`) from the start, without the barrier on retries. Show that exactly one member stays active.

**Deliverables.**

- `lost_update.md` and `deadlock.md` with the commands of each session in order (as a two-column table, like the tutorial) and the results.
- `write_skew.py`, `pyproject.toml`.
- `README.md` with the output of both runs of task 4 and an explanation of why `READ COMMITTED` breaks the rule and `SERIALIZABLE` does not.

**Done when.** The lost update and the deadlock are reproduced and explained, both fixes give a final balance of 80, the `READ COMMITTED` run leaves fewer than 1 active member, and the `SERIALIZABLE` run leaves exactly 1.

### Challenge (optional)

Folder: `exercises/08-transactions/challenge/`

**Goal.** Build a job queue in PostgreSQL that processes each job exactly once with several workers.

**Starting point.** An empty database (`./scripts/create-db.sh ch08 --reset`) with these tables:

```sql
CREATE TABLE job (
    job_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payload jsonb NOT NULL,
    status  text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'done'))
);

CREATE TABLE job_result (
    job_id       bigint NOT NULL REFERENCES job,
    worker       integer NOT NULL,
    processed_at timestamptz NOT NULL DEFAULT now()
);
```

**Tasks.**

1. `producer.py` inserts 10,000 jobs with payload `{"n": <number>}`.
2. `worker.py` loops until there are no pending jobs. In one transaction it claims a job with `SELECT ... WHERE status = 'pending' ORDER BY job_id FOR UPDATE SKIP LOCKED LIMIT 1`, processes it (sleep 1 to 5 ms and insert a row into `job_result`), sets `status = 'done'` and commits.
3. Start 8 workers at the same time and prove that every job was processed exactly once: 10,000 rows in `job_result` and no `job_id` with more than one row.
4. Add one job whose processing sleeps 30 seconds. Kill the worker that takes it (`kill -9`) while it sleeps. Show what happens to the job, its row lock and its `job_result` row, and which worker processes it afterwards.

**Deliverables.**

- `producer.py`, `worker.py`, `pyproject.toml`.
- `README.md` with the commands, the queries that prove task 3, and the evidence and explanation of task 4, including what would change if processing sent an email instead of inserting a row.

**Done when.** Task 3 shows 10,000 results with no duplicates, and task 4 shows the killed job back in `pending` and later processed by another worker.

---

## Session 09: Security

### Theory

**Least privilege**: each part of the system gets only the permissions it needs. The application reads and writes data; it does not create or drop tables. If an attacker takes over the application, they get the application's permissions, so keep them small.

PostgreSQL uses **roles** for users and groups. A typical split:

- `migrations`: owns the schema, runs migrations.
- `app`: `SELECT`, `INSERT`, `UPDATE`, `DELETE` on the tables it needs, and `USAGE` on sequences.
- `readonly`: `SELECT` only, used for reports.

`GRANT` gives privileges and `REVOKE` removes them. `ALTER DEFAULT PRIVILEGES` applies grants to tables created in the future. `REVOKE CREATE ON SCHEMA public FROM PUBLIC` stops any user from creating tables in `public` (the default since PostgreSQL 15, but say it explicitly).

**SQL injection** happens when user input is concatenated into SQL. The input becomes part of the code. With `f"... WHERE email = '{email}'"`, an input of `' OR '1'='1` returns every row. The fix is **parameterised queries**: the SQL text and the values travel separately, and the database never treats a value as code. In psycopg use `%s` placeholders; in SQLAlchemy use `text("... :email")` with parameters.

**NoSQL injection**: MongoDB filters are objects. If a login endpoint passes the request body straight into `find_one({"user": body["user"], "password": body["password"]})`, a body of `{"user": "admin", "password": {"$ne": null}}` matches any password. The fix is to validate types (the password must be a string) before building the filter.

Each engine needs authentication:

- MongoDB: a user per application with a role limited to one database (`readWrite` on `app_db`).
- Redis: ACL users (`ACL SETUSER`) with only the commands they need. Block `FLUSHALL`, `FLUSHDB`, `CONFIG` and `KEYS`.

**Secrets** (passwords, keys) go in `.env`, which is listed in `.gitignore`. Commit `.env.example` with the variable names and placeholder values. If a secret reaches Git, deleting it in a new commit is not enough: it stays in the history. Rotate the secret (change it) first, then clean the history if needed.

In `docker-compose.yml`, publish ports on `127.0.0.1` only (`"127.0.0.1:5432:5432"`), so the databases are not reachable from the network.

**Personal data** (GDPR): store only what the feature needs, and know where each personal field lives. Passwords are never stored; store a slow hash (argon2 or bcrypt).

### Tutorial

Roles on Pagila, run as the superuser:

```sql
CREATE ROLE migrations LOGIN;
CREATE ROLE app LOGIN;
CREATE ROLE readonly LOGIN;
-- set each password with: \password app

ALTER DATABASE pagila OWNER TO migrations;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO app, readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
    GRANT SELECT ON TABLES TO readonly;
```

Test it:

```sql
SET ROLE app;
DROP TABLE film;          -- ERROR: must be owner of table film
RESET ROLE;
SET ROLE readonly;
INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y');  -- ERROR: permission denied
```

Vulnerable and fixed code:

```python
# Vulnerable: input becomes SQL
cur.execute(f"SELECT * FROM customer WHERE email = '{email}'")

# Safe: input is sent as a value
cur.execute("SELECT * FROM customer WHERE email = %s", (email,))
```

```python
# SQLAlchemy
session.execute(text("SELECT * FROM customer WHERE email = :email"), {"email": email})
```

MongoDB user:

```js
use app_db
db.createUser({
  user: "app",
  pwd: passwordPrompt(),
  roles: [{ role: "readWrite", db: "app_db" }]
})
```

Redis ACL user that can read and write keys but not run dangerous commands:

```
ACL SETUSER app on >CHANGE_ME ~* +@all -@dangerous
AUTH app CHANGE_ME
SET x 1        -- OK
FLUSHALL       -- NOPERM
```

Replace `CHANGE_ME` with the value from your `.env`.

### Exercise (individual)

Folder: `exercises/09-security/exercise/`

**Goal.** Apply least privilege in the three engines and write to each of them from an API without injection.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ex09 --pagila --reset`). Roles exist for the whole PostgreSQL server, not per database, so this exercise uses the prefix `ex09_` to avoid clashing with the roles of the tutorial. For the API, use the stack you chose; `sessions/09-security/` has example projects in FastAPI, Django and Next.js. Credentials come from environment variables, never from the code.

**Tasks.**

1. `roles.sql`, run as `postgres` on `ex09`: create the login roles `ex09_migrations`, `ex09_app` and `ex09_readonly`, make `ex09_migrations` the owner of the database, remove `CREATE` on schema `public` from `PUBLIC`, and grant:
   - `ex09_app`: `SELECT`, `INSERT`, `UPDATE`, `DELETE` on every table and `USAGE` on every sequence;
   - `ex09_readonly`: `SELECT` on every table;
   - default privileges so that tables created later by `ex09_migrations` get the same grants.

2. `proofs.sql`, run as `postgres`, using `SET ROLE` and `RESET ROLE`, with the expected outcome in a comment above each statement:
   - as `ex09_app`, `DROP TABLE film` fails;
   - as `ex09_app`, `INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')` works;
   - as `ex09_readonly`, `SELECT count(*) FROM film` works;
   - as `ex09_readonly`, the same `INSERT` fails.

3. An API with 3 endpoints, each writing to one engine with the users of tasks 1 and 3:
   - `POST /actors` with body `{"first_name": string, "last_name": string}` inserts a row into `actor` with a parameterised query and returns `201` with the new `actor_id`.
   - `POST /notes` with body `{"customer_id": integer, "text": string}` inserts a document into the collection `notes` of the database `ex09`. Any other type in the body returns `422`.
   - `POST /counters/{name}` runs `INCR counter:{name}` and returns `200` with the new value. A `name` that does not match `^[a-z0-9_-]{1,32}$` returns `422`.
4. Prove that the API is safe by sending these requests and showing the response and what was stored:
   - `POST /actors` with `{"first_name": "x'); DROP TABLE actor; --", "last_name": "y"}`: the text is stored as it is and `actor` still exists;
   - `POST /notes` with `{"customer_id": 1, "text": {"$ne": null}}`: `422`;
   - `POST /counters/a*` and `POST /counters/x:y`: `422`.

**Deliverables.**

- `roles.sql`, `proofs.sql`
- The API project, with a `.env.example` listing the variables it needs.
- `README.md` with the commands to run everything, the output of `proofs.sql`, the requests and responses of task 5 (for example as `curl` commands and their output) and the output of task 6. Note that `ACL SETUSER` is lost when Redis restarts unless it is saved to an ACL file, and say how you would keep it.

**Done when.** Every proof in tasks 2 shows the expected outcome, and no query in the API is built by concatenating user input.

### Challenge (optional)

Folder: `exercises/09-security/challenge/`

**Goal.** Run the same API twice with users of different privileges and show that the database, not the code, stops the second one from writing.

**Starting point.** The API and users of the exercise above.

**Tasks.**

1. Add `GET /actors/{actor_id}`, `GET /notes?customer_id=` and `GET /counters/{name}` to the API.
2. Create read-only users: `ex09_readonly` already exists in PostgreSQL; add a MongoDB user `ex09_reader` with the role `read` on `ex09`, and a Redis ACL user `ex09_reader` that can only run `GET` on keys that start with `counter:`.
3. Run two instances of the same code: instance A on port 8001 with the users of the exercise, instance B on port 8002 with the read-only users. Only the environment variables differ.
4. Make every write endpoint return `403` when the engine refuses the write for lack of privilege: PostgreSQL SQLSTATE `42501`, a MongoDB `Unauthorized` error (code 13), or a Redis `NOPERM` error. Any other error stays a `500`.
5. Show that every `GET` works on both instances, and that every `POST` works on A and returns `403` on B.

**Deliverables.**

- The changed API project, with two example environment files (`.env.a.example` and `.env.b.example`).
- `README.md` with the commands to start both instances and the requests and responses of task 5.

**Done when.** The code has no check of which instance it is: the `403` responses come only from the privilege errors of the engines.

---

## Session 10: Backup and restore

### Theory

Data is lost through disk failure, a `DELETE` without `WHERE`, a migration that drops the wrong column, or ransomware. Replication does not protect against the last three: the mistake is replicated too.

Two numbers define a backup strategy:

- **RPO** (Recovery Point Objective): how much data you can afford to lose, measured in time. Daily backups mean an RPO of up to 24 hours.
- **RTO** (Recovery Time Objective): how long you can afford to be down while restoring.

A **logical backup** exports data as SQL or an archive (`pg_dump`). It is portable between versions and lets you restore a single table, but it is slow for very large databases. A **physical backup** copies the database files. It is faster and supports point-in-time recovery, but is tied to the PostgreSQL version.

`pg_dump` formats:

- plain (`-Fp`): a SQL script. Readable, restored with `psql`.
- custom (`-Fc`): compressed archive. Restored with `pg_restore`, which can restore selected tables and run in parallel (`-j`).
- directory (`-Fd`): one file per table; supports parallel dump.

`pg_dump` backs up one database and not roles. Use `pg_dumpall --roles-only` for roles.

Useful `pg_restore` options: `--clean` (drop objects before recreating them), `-t table` (one table), `--no-owner` (ignore original ownership), `-j 4` (parallel).

Automate backups with a script run on a schedule (cron), and keep a **retention** policy, for example 7 daily and 4 weekly copies.

A Docker volume is not a backup: `docker compose down -v` or a disk failure deletes it. A backup that has never been restored is not a backup either, because you do not know if it works. Test restores regularly in a clean environment and write the steps in a **runbook** that someone else could follow under pressure.

PostgreSQL also writes every change to the **WAL** (write-ahead log). Archiving the WAL on top of a physical backup allows **point-in-time recovery**: restoring to the moment just before the mistake. It is outside the scope of this module's practice.

### Tutorial

Back up Pagila in custom format (`-T` disables the pseudo-terminal so binary output is not corrupted):

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U postgres -Fc pagila > backups/pagila_$(date +%F_%H%M).dump
docker compose exec -T postgres pg_dumpall -U postgres --roles-only > backups/roles_$(date +%F).sql
```

Add `backups/` to `.gitignore`.

Restore into a new database:

```bash
docker compose exec -T postgres createdb -U postgres pagila_restored
time docker compose exec -T postgres pg_restore -U postgres -d pagila_restored --no-owner \
    < backups/pagila_2026-10-07_1000.dump
```

Restore a single table. Empty it first, then load only its data from the dump:

```bash
docker compose exec -T postgres psql -U postgres -d pagila -c "TRUNCATE film_actor"
docker compose exec -T postgres pg_restore -U postgres -d pagila --data-only -t film_actor \
    < backups/pagila_2026-10-07_1000.dump
```

`--clean -t film_actor` would try to drop and recreate the table, and fails because the views `actor_info` and `film_list` depend on it. `-t payment` restores nothing: `payment` is partitioned, so its rows are stored in the partitions (`payment_p2022_01`, ...), and each one has to be named.

Restore into a completely clean container to prove the backup does not depend on your existing setup:

```bash
docker run --rm -d --name pg-test -e POSTGRES_PASSWORD=test postgres:18
docker exec -i pg-test createdb -U postgres pagila
docker exec -i pg-test pg_restore -U postgres -d pagila --no-owner < backups/pagila_2026-10-07_1000.dump
docker exec -it pg-test psql -U postgres -d pagila -c "SELECT count(*) FROM rental;"
docker stop pg-test
```

A runbook entry should include: when to use it, prerequisites, exact commands, how to verify the restore (row counts, a known query), expected time, and who to tell.

### Exercise (individual)

Folder: `exercises/10-backup/exercise/`

**Goal.** Recover from a data loss with a backup, measure what was lost, and write a runbook someone else can follow.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ex10 --pagila --reset`) and these two scripts, saved in your exercise folder. Do not read ahead to fix the damage before it happens: follow the steps in order.

`activity.sql` (normal work that happens after the backup):

```sql
INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date)
SELECT customer_id, staff_id, rental_id, 1.99, timestamptz '2026-07-30 12:00+00'
FROM rental ORDER BY rental_id DESC LIMIT 5;
```

`disaster.sql` (the incident):

```sql
BEGIN;
DELETE FROM payment WHERE payment_date >= '2026-01-01';
DELETE FROM film_actor WHERE actor_id <= 50;
DELETE FROM film_category WHERE category_id = 1;
COMMIT;
```

**Tasks.**

1. Record the row counts of `payment`, `film_actor` and `film_category`.
2. Back up `ex10` in custom format into `backups/` (as in the tutorial) and note the time.
3. Run `activity.sql`, then `disaster.sql`, on `ex10`. Record the row counts again.
4. Restore the deleted data into `ex10` from your backup, without dropping or recreating the database. Time the restore. Remember that `payment` is partitioned: the rows deleted are in the partitions `payment_p2026_01` to `payment_p2026_07`. `film_actor` and `film_category` still hold part of their rows, so restoring only the missing ones needs a plan (for example `TRUNCATE` and reload, or restore into another database and copy the missing rows).
5. Record the row counts after the restore and compare them with tasks 1 and 3.
6. Write the runbook for this incident.

**Deliverables.** `runbook.md` with:

- when to use it and the prerequisites;
- every command you ran, in order, so that someone else can repeat them;
- the row counts of tasks 1, 3 and 5;
- the measured restore time (real RTO);
- the data lost between the backup and the incident (real RPO), with the query that shows it;
- how to verify the restore;
- what you would change in your backup strategy to lose less.

**Done when.** After the restore, the three tables have the same row counts as in task 1, the 5 payments of `activity.sql` are identified as lost, and the runbook can be followed without your help.

### Challenge (optional)

Folder: `exercises/10-backup/challenge/`

**Goal.** Automate backups with retention and check every backup by restoring it.

**Starting point.** The `pagila` database and the tutorial of this session.

**Tasks.**

1. `backup.sh` takes a custom-format dump of `pagila` named `pagila_YYYY-MM-DD_HHMM.dump` and, next to it, a file `pagila_YYYY-MM-DD_HHMM.counts` with the row count of every table at the time of the dump. It then applies a retention policy: keep the latest backup of each of the last 7 days, and the latest backup of each of the last 4 weeks; delete the rest. Accept an optional `--now YYYY-MM-DD` argument that replaces today's date, so that the retention can be tested without waiting weeks.
2. `verify.sh` restores the latest dump into a throwaway container (`docker run --rm ... postgres:18`), counts the rows of every table, compares them with the `.counts` file of that dump, prints every difference and exits with a non-zero code if there is any.
3. Test the retention: create backups for 40 simulated days with `--now` and show which files remain.
4. Schedule both scripts (cron on Linux and macOS, Task Scheduler or a loop in WSL on Windows) and show the log of two scheduled runs.

**Deliverables.**

- `backup.sh`, `verify.sh`.
- `README.md` with the schedule configuration, the list of files left by task 3, the log of task 4, and the output of `verify.sh` for a good dump and for a dump you changed on purpose.

**Done when.** After task 3 exactly the expected files remain (at most 7 daily and 4 weekly), `verify.sh` exits with 0 for a good dump and with a non-zero code for a changed one.

---

## Session 11: ORM I, SQLAlchemy

### Theory

An **ORM** (Object-Relational Mapper) maps tables to classes and rows to objects. You write Python, and the ORM generates SQL.

What you gain: less repetitive code, type hints, relationships navigated as attributes, and parameterised queries by default (protection against injection).

What it costs: the SQL is hidden, so it is easy to generate slow or numerous queries without noticing. Some database features are awkward to express. The abstraction leaks: you still need to know SQL to understand what happens.

SQLAlchemy 2.0 building blocks:

- `Engine`: the connection pool to a database.
- `Session`: a unit of work. It tracks objects you load or add, and sends changes on `commit()`.
- `DeclarativeBase`: the base class for your models.
- `Mapped[...]` and `mapped_column(...)`: typed column definitions.
- `relationship(...)`: navigation between models (`customer.rentals`).
- `select(Model).where(...).join(...).group_by(...)`: queries in the 2.0 style.

`create_engine(..., echo=True)` logs every SQL statement. Keep it on while developing.

The **N+1 problem**: you load N objects with one query, then access a relationship on each one. By default relationships load lazily, so each access runs another query: 1 + N queries instead of 1 or 2. With 20 rows it is invisible; with 2,000 it is slow.

**Eager loading** fixes it:

- `selectinload(Model.rel)`: a second query with `WHERE id IN (...)`. Good for collections (1:N).
- `joinedload(Model.rel)`: a `JOIN` in the same query. Good for single objects (N:1).

For complex reports, plain SQL is often clearer. Use `text()` with bound parameters.

If you used Django in Project I: Django's `select_related` corresponds to `joinedload`, and `prefetch_related` to `selectinload`.

### Tutorial

```bash
uv init --bare
uv add "sqlalchemy>=2" "psycopg[binary]"
export DATABASE_URL="postgresql+psycopg://app:<password>@localhost:5432/pagila"
```

```python
import os
from datetime import datetime
from sqlalchemy import ForeignKey, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    rentals: Mapped[list["Rental"]] = relationship(back_populates="customer")


class Rental(Base):
    __tablename__ = "rental"
    rental_id: Mapped[int] = mapped_column(primary_key=True)
    rental_date: Mapped[datetime]
    return_date: Mapped[datetime | None]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.customer_id"))
    customer: Mapped[Customer] = relationship(back_populates="rentals")


engine = create_engine(os.environ["DATABASE_URL"], echo=True)

with Session(engine) as session:
    # N+1: one query for customers, then one per customer
    customers = session.scalars(select(Customer).limit(20)).all()
    for c in customers:
        print(c.first_name, len(c.rentals))

    # Fixed: two queries in total
    stmt = select(Customer).options(selectinload(Customer.rentals)).limit(20)
    for c in session.scalars(stmt):
        print(c.first_name, len(c.rentals))

    # Aggregation in the ORM
    stmt = (
        select(Customer.last_name, func.count(Rental.rental_id).label("n"))
        .join(Customer.rentals)
        .group_by(Customer.customer_id)
        .order_by(func.count(Rental.rental_id).desc())
        .limit(5)
    )
    for row in session.execute(stmt):
        print(row.last_name, row.n)
```

Count the `SELECT` statements in the log for each block. Run the fixed version in a new session: in the same session the rentals are already loaded, so the comparison would be unfair.

### Exercise (individual)

Folder: `exercises/11-orm/exercise/`

**Goal.** Map existing tables to ORM models, compare generated SQL with handwritten SQL, and find and fix an N+1.

**Starting point.** A fresh copy of Pagila and a uv project:

```bash
./scripts/create-db.sh ex11 --pagila --reset
uv init --bare
uv add "sqlalchemy>=2" "psycopg[binary]"
```

**Tasks.**

1. Map these 6 tables with SQLAlchemy 2.0 models (`Mapped`, `mapped_column`) and their relationships: `film`, `language`, `actor`, `film_actor`, `category`, `film_category`. `Film` must have `language`, `actors` and `categories`; `Actor` and `Category` must have `films`.
2. Write these 3 queries with the ORM, run them with `echo=True`, and compare the SQL the ORM generates with the handwritten SQL below:

   ```sql
   -- Q1: number of films per category, most films first
   SELECT c.name, count(*) AS films
   FROM category c JOIN film_category fc ON fc.category_id = c.category_id
   GROUP BY c.category_id, c.name
   ORDER BY films DESC, c.name;

   -- Q2: films longer than the average film
   SELECT f.film_id, f.title, f.length
   FROM film f
   WHERE f.length > (SELECT avg(length) FROM film)
   ORDER BY f.length DESC, f.film_id;

   -- Q3: the 10 actors with most films
   SELECT a.actor_id, a.first_name, a.last_name, count(*) AS films
   FROM actor a JOIN film_actor fa ON fa.actor_id = a.actor_id
   GROUP BY a.actor_id
   ORDER BY films DESC, a.actor_id
   LIMIT 10;
   ```

3. Create an N+1 on purpose: load the first 100 films by `film_id` and print each title with the names of its actors through `film.actors`. Count the `SELECT` statements. Fix it with eager loading and count again, in a new session.

**Deliverables.**

- `models.py`, `queries.py`, `n_plus_one.py`, `pyproject.toml`.
- `README.md` with the commands to run each script, the handwritten and generated SQL of each query side by side with the differences you notice, and the number of queries before and after the fix.

**Done when.** The 3 ORM queries return the same rows as the handwritten SQL, the N+1 version runs 101 queries, and the fixed version runs at most 2.

### Challenge (optional)

Folder: `exercises/11-orm/challenge/`

**Goal.** Turn the absence of N+1 into an automated test.

**Starting point.** The models of the exercise above (or your own models of the same 6 tables) and `uv add pytest`.

**Tasks.**

1. In `tests/conftest.py`, write a pytest fixture that counts the SQL statements an engine runs, using SQLAlchemy's `before_cursor_execute` event.
2. Write a helper `assert_max_queries(n)`, used as a context manager, that fails the test if more than `n` statements ran inside the `with` block.
3. In `tests/test_queries.py`, write a test that lists the first 100 films with their actors and their categories inside `assert_max_queries(3)`.
4. Remove the eager loading from the query, run the test and show it failing with the number of statements. Put the eager loading back.

**Deliverables.**

- `tests/conftest.py`, `tests/test_queries.py` and the code they test.
- `README.md` with `uv run pytest -v` output for the passing test and for the failing one.

**Done when.** The test passes with eager loading and fails without it, and the failure message shows how many statements ran.

---

## Session 12: ORM II, migrations, transactions and API

### Theory

A schema changes throughout a project's life. **Migrations** are versioned scripts that move the schema from one version to the next (`upgrade`) and back (`downgrade`). Everyone, including production, applies the same steps in the same order. **Alembic** is the migration tool for SQLAlchemy.

`alembic revision --autogenerate` compares your models with the database and writes a migration. Always read it before applying. Autogenerate does not detect renamed tables or columns (it sees a drop and an add, which loses data), some changes to constraints and types, and anything that is not in your models (views, triggers, data).

A **schema migration** changes structure. A **data migration** changes rows (filling a new column, splitting a field). Adding a `NOT NULL` column to a table that already has rows fails unless you give it a default, or do it in steps: add the column as nullable, fill it, then set `NOT NULL`.

If the database already exists (for example Pagila, or a schema created earlier with SQL scripts), create a baseline migration that matches it, mark the database as being at that version with `alembic stamp head`, then use Alembic for every change after. Running `--autogenerate` against an existing database whose tables are not all mapped proposes dropping every table it does not know; read the generated file before you apply anything.

Transactions in the ORM:

- `with session.begin():` commits at the end of the block, or rolls back if an exception is raised.
- `select(...).with_for_update()` generates `SELECT ... FOR UPDATE`.

In a web API, each request gets its own session, closed at the end of the request. In FastAPI this is a dependency (`get_session`) injected into each endpoint. Request and response bodies are defined with Pydantic models, which validate input before your code runs. When a request breaks a business rule (insufficient balance, username already taken), return `409 Conflict`, not `500`.

The engine keeps a **connection pool**, reusing connections instead of opening one per request. The pool size limits how many requests can talk to the database at once.

### Tutorial

```bash
uv add alembic fastapi "uvicorn[standard]"
uv run alembic init migrations
```

In `migrations/env.py`, set `target_metadata = Base.metadata` and read the URL from `DATABASE_URL`.

```bash
uv run alembic revision --autogenerate -m "initial schema"
# read the generated file in migrations/versions/
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

Adding a required column in three steps (a data migration in the middle):

```python
def upgrade():
    op.add_column("customer", sa.Column("tier", sa.Text(), nullable=True))
    op.execute("UPDATE customer SET tier = CASE WHEN active = 1 THEN 'standard' ELSE 'inactive' END")
    op.alter_column("customer", "tier", nullable=False)


def downgrade():
    op.drop_column("customer", "tier")
```

A FastAPI endpoint with a transaction and a row lock (assumes the `balance` column from exercise 08, mapped on `Customer`):

```python
from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

SessionLocal = sessionmaker(engine)
app = FastAPI()


def get_session():
    with SessionLocal() as session:
        yield session


class Charge(BaseModel):
    amount: Decimal = Field(gt=0)


@app.post("/customers/{customer_id}/charge")
def charge(customer_id: int, body: Charge, session: Session = Depends(get_session)):
    with session.begin():
        customer = session.scalars(
            select(Customer).where(Customer.customer_id == customer_id).with_for_update()
        ).one_or_none()
        if customer is None:
            raise HTTPException(404, "Customer not found")
        if customer.balance < body.amount:
            raise HTTPException(409, "Insufficient balance")
        customer.balance -= body.amount
    return {"customer_id": customer_id, "balance": customer.balance}
```

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to call the endpoint.

### Exercise (individual)

Folder: `exercises/12-api/exercise/`

**Goal.** Evolve an existing schema with reversible migrations and expose a transactional API that stays correct under concurrent requests.

**Starting point.** A fresh copy of Pagila and a uv project:

```bash
./scripts/create-db.sh ex12 --pagila --reset
uv init --bare
uv add "sqlalchemy>=2" "psycopg[binary]" alembic fastapi "uvicorn[standard]" httpx
```

Map at least `customer`, `film`, `inventory`, `rental` and `staff`. You can reuse the models of exercise 11.

**Tasks.**

1. Baseline. Initialise Alembic, create a migration `0001_baseline` with empty `upgrade` and `downgrade`, and run `alembic stamp head` on `ex12`. Configure `include_object` in `migrations/env.py` so that `--autogenerate` ignores tables you did not map. In the README, explain what `--autogenerate` would have generated without the baseline and without `include_object`, and why that is dangerous.
2. Migration `0002_loyalty_points`: add `customer.loyalty_points integer NOT NULL`, filled with the customer's number of rentals, in three steps (add as nullable, fill, set `NOT NULL`), with `server_default` 0 for new rows. `downgrade` removes the column. Expected: customer 1 has 66 points.
3. Migration `0003_one_open_rental_per_copy`: three copies (`inventory_id` 1358, 1435 and 2408) have two open rentals each. Close the older open rental of each one by setting its `return_date` to the `rental_date` of the newer one, then create the partial unique index `rental_one_open_per_copy` on `rental (inventory_id) WHERE return_date IS NULL`. `downgrade` drops the index only. In the README, explain why the data fix is not undone.
4. Show `alembic upgrade head`, `alembic downgrade base` and `alembic upgrade head` again running without errors, with `\d customer` and `\d rental` after each.
5. An API with 3 endpoints, each request with its own session:
   - `POST /rentals` with body `{"customer_id": int, "film_id": int, "store_id": int, "staff_id": int}`. In one transaction, find a copy of the film in that store with no open rental, lock it with `with_for_update(skip_locked=True)` and insert the rental with `rental_date` now. Returns `201` with `rental_id` and `inventory_id`, `404` if the customer or the film does not exist, and `409` if no copy is available. If the insert violates `rental_one_open_per_copy` (another request rented the same copy between your read and your insert), retry the whole transaction, at most 3 times, before returning `409`.
   - `POST /rentals/{rental_id}/return` sets `return_date` to now. Returns `200`, `404` if the rental does not exist, and `409` if it was already returned.
   - `GET /rentals/overdue?as_of=2026-07-31` lists open rentals whose due date (`rental_date` plus the film's `rental_duration` in days) is before `as_of`, ordered by `rental_date`. Each item has `rental_id`, `rental_date`, `due_date`, `customer` (`customer_id`, `first_name`, `last_name`) and `film` (`film_id`, `title`). It must not have an N+1. Expected on a fresh copy after the migrations: 229 items.
6. `concurrency_test.py` sends 5 simultaneous `POST /rentals` for film 7 in store 1 (customers 1 to 5, staff 6). Film 7 has exactly 2 copies in store 1, both available on a fresh copy. Expected: exactly two `201` and three `409`, with two different `inventory_id`.

**Deliverables.**

- The project: models, `migrations/`, `app/`, `concurrency_test.py`, `pyproject.toml`.
- `README.md` with the commands to run the migrations, the API and the test, the output of tasks 4 and 6, the number of SQL statements `GET /rentals/overdue` runs (from the `echo=True` log), and the explanations asked in tasks 1 and 3.

**Done when.** The migrations go up, down and up again without errors, the endpoints return the status codes above, the overdue list has 229 items in a fixed number of queries, and the concurrency test gives two `201` and three `409` every time you run it on a fresh copy.

### Challenge (optional)

Folder: `exercises/12-api/challenge/`

**Goal.** Rename a column used by a running API without downtime, using the expand and contract pattern.

**Starting point.** The project of the exercise above. The column to rename is `customer.email`, which becomes `customer.email_address`.

**Tasks.**

1. Add two endpoints and keep them in two versions of the API, in separate modules that run as separate processes: version 1 on port 8001 uses `email`, version 2 on port 8002 uses `email_address`.
   - `GET /customers/{customer_id}` returns the customer with its email.
   - `PUT /customers/{customer_id}/email` with body `{"email": string}` changes it.
2. Migration `expand`: add `email_address`, backfill it from `email`, and create a trigger that copies a change made to either column into the other.
3. With both versions running, change an email through version 1 and read it through version 2, then the other way round.
4. Migration `contract`: after stopping version 1, drop the trigger and the column `email`. Show that version 2 still works.
5. Show that `downgrade` of each migration works.

**Deliverables.**

- The two migrations, both API versions, and `check_versions.sh` (or `.py`) that runs the requests of task 3.
- `README.md` with the order of deployment steps and the output of `check_versions` after the expand migration and of version 2 after the contract migration.

**Done when.** After the expand migration a change made through either version is visible in the other, and after the contract migration version 2 works and `email` no longer exists.

---

## Session 13: MongoDB I, documents, CRUD and validation

### Theory

MongoDB stores **documents** (stored as BSON, a binary form of JSON with extra types such as dates and decimals) in **collections**. Each document has an `_id`, by default an `ObjectId` generated by the client, which also encodes its creation time. Documents in the same collection do not have to share a shape.

The key modelling decision is **embed or reference**:

- **Embed** (put data inside the parent document) when it is read together with the parent, belongs to it, and has a bounded size. Example: the address of a store, the lines of an order.
- **Reference** (store an ID and look it up separately) when the data is shared by many parents, grows without limit, or is often read on its own. Example: the full rental history of a customer.

A document has a hard limit of 16 MB. A list that grows forever (every rental, every log line) will eventually hit it and will slow down every read before that. A common compromise is to embed the latest N items and reference the rest.

CRUD:

- `insertOne`, `insertMany`
- `find(filter, projection)` with operators: `$eq`, `$gt`, `$lt`, `$in`, `$exists`, `$elemMatch` (one array element must match several conditions)
- `updateOne`, `updateMany` with update operators: `$set`, `$unset`, `$inc`, `$push`, `$addToSet`; `{ upsert: true }` to insert when nothing matches
- `deleteOne`, `deleteMany`

Without validation, any shape is accepted. `$jsonSchema` validation rejects documents that do not match the declared fields and types. `validationLevel` (`strict` or `moderate`) controls whether existing invalid documents are checked on update; `validationAction` (`error` or `warn`) controls whether invalid writes are rejected or only logged.

Indexes work as in PostgreSQL: single field, compound (order matters), and **multikey** (an index on an array field indexes every element). `explain("executionStats")` shows `COLLSCAN` (full scan) or `IXSCAN` (index), and `totalDocsExamined` compared with `nReturned`.

MongoDB is a poor fit for highly relational data that needs transactions across many entities on every operation. That data belongs in PostgreSQL.

### Tutorial

```bash
uv add pymongo
```

In `mongosh`:

```js
use pagila_docs

db.stores.insertOne({
  _id: 1,
  manager: { staff_id: 1, name: "Mike Hillyer" },
  address: { line: "47 MySakila Drive", city: "Lethbridge", country: "Canada" },
  staff: [{ staff_id: 1, name: "Mike Hillyer" }],
  opened_at: new Date("2006-02-15")
})

db.stores.find({ "address.country": "Canada" }, { _id: 1, "address.city": 1 })

db.stores.updateOne({ _id: 1 }, { $push: { staff: { staff_id: 3, name: "New Hire" } } })
db.stores.updateOne({ _id: 1 }, { $inc: { visits: 1 } })   // creates the field if missing
```

Add validation:

```js
db.runCommand({
  collMod: "stores",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["manager", "address"],
      properties: {
        manager: { bsonType: "object", required: ["staff_id", "name"] },
        address: {
          bsonType: "object",
          required: ["city", "country"],
          properties: { city: { bsonType: "string" }, country: { bsonType: "string" } }
        },
        staff: { bsonType: "array" }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
})

db.stores.insertOne({ _id: 99, address: { city: 42 } })   // rejected: Document failed validation
```

Index and explain:

```js
db.stores.find({ "address.country": "Canada" }).explain("executionStats")
db.stores.createIndex({ "address.country": 1 })
db.stores.find({ "address.country": "Canada" }).explain("executionStats")
```

From Python, reading from PostgreSQL and writing documents:

```python
import os
import psycopg
from pymongo import MongoClient

mongo = MongoClient(os.environ["MONGO_URL"])["pagila_docs"]

with psycopg.connect(os.environ["DATABASE_URL"]) as pg:
    rows = pg.execute("""
        SELECT s.store_id, a.address, c.city, co.country
        FROM store s
        JOIN address a  ON a.address_id = s.address_id
        JOIN city c     ON c.city_id = a.city_id
        JOIN country co ON co.country_id = c.country_id
    """).fetchall()

for store_id, line, city, country in rows:
    mongo.stores.update_one(
        {"_id": store_id},
        {"$set": {"address": {"line": line, "city": city, "country": country}}},
        upsert=True,
    )
```

### Exercise (individual)

Folder: `exercises/13-mongo/exercise/`

**Goal.** Turn relational data into documents, choosing what to embed and what to reference, and query, validate and index them.

**Starting point.** A fresh copy of Pagila (`./scripts/create-db.sh ex13 --pagila --reset`), the MongoDB database `pagila_docs`, and a uv project:

```bash
uv init --bare
uv add pymongo "psycopg[binary]"
```

The script reads `DATABASE_URL` and `MONGO_URL` from the environment (see `.env.example`). The collections must have these shapes. In this version of Pagila a film can belong to more than one category, so `categories` is an array. Store money as `Decimal128` and dates as BSON dates.

`films` (one document per film, 1,000 documents):

```json
{
  "_id": 1,
  "title": "ACADEMY DINOSAUR",
  "release_year": 2012,
  "language": "English",
  "rating": "PG",
  "length": 86,
  "rental_duration": 6,
  "rental_rate": { "$numberDecimal": "0.99" },
  "categories": ["Games", "New", "Travel"],
  "actors": [{ "actor_id": 1, "name": "PENELOPE GUINESS" }, { "actor_id": 10, "name": "CHRISTIAN GABLE" }]
}
```

`customers` (one document per customer, 999 documents; `recent_rentals` holds the 10 most recent rentals, ordered by `rental_date` descending and then `rental_id` descending):

```json
{
  "_id": 1,
  "first_name": "MARY",
  "last_name": "SMITH",
  "email": "MARY.SMITH@sakilacustomer.org",
  "store_id": 1,
  "address": { "city": "Sasebo", "country": "Japan" },
  "rental_count": 66,
  "recent_rentals": [
    { "rental_id": 87420, "film_id": 307, "title": "FELLOWSHIP AUTUMN",
      "rental_date": { "$date": "2026-07-23T01:38:34.193Z" }, "return_date": null }
  ]
}
```

`rentals` (one document per rental, 51,805 documents; `amount` is the sum of the payments of that rental, 0 when there are none):

```json
{
  "_id": 87420,
  "customer_id": 1,
  "film_id": 307,
  "title": "FELLOWSHIP AUTUMN",
  "categories": ["Children", "Family", "Sci-Fi"],
  "store_id": 1,
  "rental_date": { "$date": "2026-07-23T01:38:34.193Z" },
  "return_date": null,
  "amount": { "$numberDecimal": "0" }
}
```

The examples are film 1, customer 1 and the most recent rental of customer 1 (some arrays are shortened).

**Tasks.**

1. `load.py` reads Pagila and writes the three collections. Running it twice must leave the same documents (use the Pagila IDs as `_id` and upserts or `replace_one`). In the README, justify why actors and categories are embedded in `films`, why only 10 rentals are embedded in `customers`, and why the full history is in `rentals`.
2. Write these 8 operations in `operations.js` (for `mongosh`) and record the result of each one:
   1. films rated `PG-13` and longer than 120 minutes. Expected: 118 documents.
   2. films in which actor 1 appears. Expected: 19 documents.
   3. films in the category `Horror` with a rental rate of 0.99. Expected: 43 documents.
   4. customers with at least one rental not returned among their `recent_rentals` (use `$elemMatch`). Expected: 56 documents.
   5. customer 1 with only `first_name`, `last_name` and the titles of `recent_rentals` (projection). Expected: 1 document with 10 titles.
   6. raise by 0.50 the rental rate of films rated `NC-17` shorter than 60 minutes (`updateMany` with `$inc`). Expected: 21 documents modified.
   7. add a rental to the front of customer 1's `recent_rentals` and keep only 10 (`$push` with `$each`, `$position` and `$slice`). Expected: `recent_rentals` still has 10 items and the first one is the new rental.
   8. an `updateOne` with `upsert: true` and `$setOnInsert` that creates the film `{_id: 1001, title: "TEST FILM"}`, run twice. Expected: the first run upserts 1 document; the second matches 1 and modifies 0.
3. Add `$jsonSchema` validation to `films` (`validationLevel: "strict"`, `validationAction: "error"`): `title` string, `rating` one of `G`, `PG`, `PG-13`, `R`, `NC-17`, `length` integer between 1 and 999, `rental_rate` decimal, `categories` array of strings, `actors` array of objects with `actor_id` integer and `name` string. Show that `load.py` still runs, and that a document with `rating: "XXX"` and one with `length: "long"` are rejected.
4. Run `find({"actors.actor_id": 1}).explain("executionStats")` before and after creating an index on `actors.actor_id`, and compare `stage`, `totalDocsExamined` and `nReturned`.

**Deliverables.**

- `load.py`, `pyproject.toml`, `operations.js`, `validation.js`, `index.js`.
- `README.md` with the commands to run each file, the justifications of task 1, the result of each operation, the rejected inserts with their error and the two `explain` summaries.

**Done when.** The three collections have 1,000, 999 and 51,805 documents, every operation returns the expected result on freshly loaded collections, both invalid documents are rejected, and the plan changes from `COLLSCAN` to `IXSCAN` with 19 documents examined.

### Challenge (optional)

Folder: `exercises/13-mongo/challenge/`

**Goal.** Store a history that grows without limit with the bucket pattern, and measure the difference.

**Starting point.** The `rentals` collection of the exercise above (or `load.py` run again).

**Tasks.**

1. Design the collection `rental_buckets`: each document holds at most 50 rentals of one customer, with `customer_id`, a sequence number `seq`, a `count` and an array `rentals`.
2. Write `add_rental(customer_id, rental)` that adds a rental to the customer's open bucket, or opens a new one, with a single `updateOne` with `upsert: true` and a filter on `count`. Explain what makes it safe when two calls for the same customer run at the same time, and what you need (for example a unique index) to keep it safe.
3. Fill `rental_buckets` from `rentals` with `add_rental`, in `rental_date` order.
4. Build a second collection `rental_history` with one document per customer embedding every rental.
5. For customer 380 (97 rentals, the most in Pagila), compare the document sizes (`Object.bsonsize`) and the time to read the 20 most recent rentals from each collection.

**Deliverables.**

- `buckets.py` (or `.js`) with the functions and the loading code.
- `README.md` with the design, the explanation of task 2, and the sizes and times of task 5.

**Done when.** No bucket has more than 50 rentals, customer 380 has two buckets (50 and 47 rentals), and the README explains when the bucket pattern pays off.

---

## Session 14: MongoDB II, aggregation pipelines and reports

### Theory

An **aggregation pipeline** is a list of stages. Each stage receives documents, transforms them, and passes the result to the next.

- `$match`: filter. Put it as early as possible so later stages handle fewer documents and an index can be used.
- `$group`: group by a key with accumulators (`$sum`, `$avg`, `$min`, `$max`, `$push`, `$addToSet`, `$first`).
- `$project` / `$set`: choose, rename or compute fields.
- `$unwind`: turn one document with an array of N items into N documents, one per item.
- `$sort`, `$limit`, `$skip`.
- `$lookup`: join with another collection. It works, but if you need it on every query, the data is probably better embedded or in PostgreSQL.
- `$facet`: run several sub-pipelines on the same input and return all results in one document (for example totals, a histogram and a top 5).
- `$bucket`: group numeric values into ranges you define.
- `$dateTrunc`: round dates to a unit (day, week, month) for time series.

`$out` replaces a whole collection with the pipeline result. `$merge` inserts or updates documents in a target collection, which lets you refresh a report incrementally.

A **frozen report** is generated once from the source data and never changes afterwards, even if the source is corrected later. A monthly sales report sent to an accountant must stay as it was sent. The process: read from PostgreSQL with the `readonly` role, build the document, write it to MongoDB with a deterministic `_id` (such as `"2026-09"`) so it cannot be written twice.

Backup in MongoDB: `mongodump --archive --gzip` writes a single compressed file; `mongorestore --archive --gzip --drop` restores it, replacing existing collections.

MongoDB supports multi-document transactions (on a replica set). If you need them on most operations, the data is probably relational.

### Tutorial

Films per rating with average rental rate:

```js
db.films.aggregate([
  { $group: { _id: "$rating", films: { $sum: 1 }, avg_rate: { $avg: "$rental_rate" } } },
  { $sort: { films: -1 } }
])
```

The 10 actors with most films (`$unwind` the embedded array):

```js
db.films.aggregate([
  { $unwind: "$actors" },
  { $group: { _id: "$actors.actor_id", name: { $first: "$actors.name" }, films: { $sum: 1 } } },
  { $sort: { films: -1 } },
  { $limit: 10 }
])
```

Rentals per month from the embedded rentals in `customers`:

```js
db.customers.aggregate([
  { $unwind: "$recent_rentals" },
  { $group: {
      _id: { $dateTrunc: { date: "$recent_rentals.rental_date", unit: "month" } },
      rentals: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
])
```

A frozen monthly report generated from PostgreSQL:

```python
from datetime import UTC, datetime
from pymongo.errors import DuplicateKeyError

month = "2022-07"
with psycopg.connect(os.environ["READONLY_DATABASE_URL"]) as pg:
    rows = pg.execute("""
        SELECT st.store_id, count(*) AS payments, sum(p.amount) AS revenue
        FROM payment p
        JOIN staff st ON st.staff_id = p.staff_id
        WHERE to_char(p.payment_date, 'YYYY-MM') = %s
        GROUP BY st.store_id
    """, (month,)).fetchall()

report = {
    "_id": month,
    "generated_at": datetime.now(UTC),
    "stores": [{"store_id": s, "payments": n, "revenue": str(r)} for s, n, r in rows],
}
try:
    mongo.monthly_reports.insert_one(report)
except DuplicateKeyError:
    print(f"Report {month} already exists and is frozen")
```

Backup and restore (credentials from `.env`):

```bash
docker compose exec -T mongo mongodump --uri "mongodb://<user>:<password>@localhost:27017/?authSource=admin" \
    --db pagila_docs --archive --gzip > backups/mongo_$(date +%F).archive.gz

docker compose exec -T mongo mongorestore --uri "mongodb://<user>:<password>@localhost:27017/?authSource=admin" \
    --archive --gzip --drop < backups/mongo_2026-10-07.archive.gz
```

### Exercise (individual)

Folder: `exercises/14-pipelines/exercise/`

**Goal.** Build reports with aggregation pipelines, and back up and restore a MongoDB database.

**Starting point.** The collections `films` and `rentals` in `pagila_docs`, with the shapes given in the exercise of session 13, loaded from a fresh copy of Pagila and not changed afterwards. If you changed them, drop them and load them again.

**Tasks.** Write each pipeline in `pipelines.js` (for `mongosh`):

1. Revenue per category per month in 2025, by `rental_date`, from `rentals`. Output: `category`, `month`, `revenue`, sorted by category and month. Expected: 192 documents; `Action` in January 2025 has 333.87. In the README, explain why this value differs from question 2 of exercise 05 (314.94).
2. The actor with most films in each category, from `films`, including ties. Output: one document per category with `category`, `films` and an array `actors`. Expected: 16 documents with 30 actors in total.
3. The distribution of film lengths with `$bucket` and boundaries `[0, 60, 90, 120, 150, 186]`. Expected counts: 96, 224, 214, 216 and 250.
4. One `$facet` over `films` with three summaries: the total number of films and the average rental rate; the number of films per rating; the 5 longest films (`title`, `length`), ties broken by title. Expected: 1,000 films with an average rate of 2.98; G 178, PG 194, PG-13 223, R 195, NC-17 210; the 5 longest are `CHICAGO NORTH`, `CONTROL ANTHEM`, `DARN FORRESTER`, `GANGS PRIDE` and `HOME PITY`, all with 185 minutes.
5. `backup_mongo.sh` dumps `pagila_docs` to `backups/` as a compressed archive with a dated name (as in the tutorial). `restore_mongo.sh` restores the latest archive into a database called `pagila_docs_restored` (use `--nsFrom 'pagila_docs.*' --nsTo 'pagila_docs_restored.*'`) and prints the document count of each collection in both databases.

**Deliverables.**

- `pipelines.js`, `backup_mongo.sh`, `restore_mongo.sh`.
- `README.md` with the commands, the first documents of each pipeline result with its document count, the explanation asked in task 1, and the output of `restore_mongo.sh`.

**Done when.** Each pipeline returns the expected result, and the restored database has the same document count as the original in every collection.

### Challenge (optional)

Folder: `exercises/14-pipelines/challenge/`

**Goal.** Keep a report up to date incrementally with `$merge`, so that each run is cheap and running it again changes nothing.

**Starting point.** The `rentals` collection of the exercise of session 13.

**Tasks.**

1. `daily_revenue.js` (or `.py`) builds the collection `daily_revenue` with one document per day: `_id` (the day), `rentals` and `revenue`, using `$merge` with `whenMatched: "replace"`.
2. Track a watermark in a collection `report_state`: the highest `rentals._id` processed. Each run finds the days of the rentals with `_id` above the watermark, recomputes only those days from all their rentals, merges them, and then moves the watermark.
3. Write a test that:
   1. runs the report on the full collection;
   2. inserts 5 new rentals into `rentals`, with `_id` above the current maximum: 3 on `2026-07-28` (a day that already has rentals) and 2 on `2026-07-29` (a new day);
   3. runs the report again and checks that only those 2 days changed;
   4. compares `daily_revenue` with a full recomputation from scratch;
   5. runs the report a third time and checks that nothing changed.

**Deliverables.**

- The report script and the test.
- `README.md` with how to run them, the output of the test, and why recomputing a whole day is safer than adding the new amounts to it.

**Done when.** The test passes: the second run touches only 2 days, the result equals a full recomputation, and the third run changes nothing.

---

## Session 15: Redis I, data structures and patterns

### Theory

Redis keeps all data in memory and runs commands one at a time on a single thread. Each command is therefore **atomic**: no other command runs in the middle of it. This makes counters and similar updates safe under concurrency without locks.

Data structures and typical uses:

- **String**: a value, a cached JSON blob, or a counter (`INCR`, `INCRBY`).
- **Hash**: a small object with fields (`HSET user:1 name Ana plan pro`).
- **List**: ordered, push and pop at both ends. A simple queue (`LPUSH` / `BRPOP`).
- **Set**: unique members. Tags, unique visitors per day, deduplication, membership checks (`SISMEMBER`).
- **Sorted set**: unique members with a numeric score, kept in order by score. Anything ordered by a number: timestamps, prices, scores (`ZADD`, `ZINCRBY`, `ZRANGE`, `ZREMRANGEBYRANK`).

**Expiry**: `EXPIRE key seconds` sets a time to live, `TTL key` shows the remaining time, `PERSIST key` removes it. `SET key value NX EX 30` sets the key only if it does not exist, with a 30-second expiry, in one atomic command. Only one client gets `OK`, and the key disappears on its own if that client crashes. This is the basis of simple locks and idempotency keys.

Common patterns:

- **Cache-aside**: read from Redis; on a miss, read from the database and store the result with a TTL. When the source changes, delete the cache key.
- **Capped timeline**: a sorted set with timestamps as scores, trimmed to the latest N items after each insert.
- **Lock with expiry**: `SET lock:name owner NX EX seconds`. Release it only if you still own it, otherwise you may delete a lock another process acquired after yours expired.
- **Queue**: list with `LPUSH` and `BRPOP`.
- **Rate limit**: counter per client per time window, with expiry.

Name keys with a convention such as `object:id:field` (`film:42:views`) and document it. Never use `KEYS *` in production: it blocks Redis while scanning every key. Use `SCAN` instead.

A **pipeline** sends several commands in one round trip, which is faster but not atomic. `MULTI` / `EXEC` runs a group of commands atomically.

### Tutorial

In `redis-cli`:

```
INCR film:42:views
INCR film:42:views
GET film:42:views                          -- "2"

HSET film:42 title "ACADEMY DINOSAUR" rate 0.99
HGETALL film:42

SADD visitors:2026-10-07 customer:5 customer:9 customer:5
SCARD visitors:2026-10-07                  -- 2

ZINCRBY search:terms "alien" 1
ZINCRBY search:terms "matrix" 3
ZRANGE search:terms 0 4 REV WITHSCORES     -- most searched terms

SET lock:nightly-export worker-a NX EX 30  -- OK
SET lock:nightly-export worker-b NX EX 30  -- (nil): someone holds it
TTL lock:nightly-export
```

From Python:

```python
import json
import os
import time
import uuid
import redis

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def get_customer(customer_id: int) -> dict:
    key = f"cache:customer:{customer_id}"
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)
    data = load_customer_from_postgres(customer_id)
    r.set(key, json.dumps(data), ex=300)
    return data


def update_customer(customer_id: int, changes: dict) -> None:
    save_customer_to_postgres(customer_id, changes)
    r.delete(f"cache:customer:{customer_id}")


release = r.register_script("""
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
""")


def run_exclusively(name: str, job) -> bool:
    token = str(uuid.uuid4())
    if not r.set(f"lock:{name}", token, nx=True, ex=60):
        return False
    try:
        job()
    finally:
        release(keys=[f"lock:{name}"], args=[token])
    return True


def allow_request(client_id: str, limit: int = 10) -> bool:
    window = int(time.time() // 60)
    key = f"ratelimit:{client_id}:{window}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    count, _ = pipe.execute()
    return count <= limit
```

### Exercise (individual)

Folder: `exercises/15-redis/exercise/`

**Goal.** Implement four common Redis patterns on Pagila data and show each one working.

**Starting point.** A fresh copy of Pagila and a uv project. The scripts read `DATABASE_URL` and `REDIS_URL` from the environment (see `.env.example`).

```bash
./scripts/create-db.sh ex15 --pagila --reset
uv init --bare
uv add redis "psycopg[binary]"
```

Create this materialised view in `ex15` (it is the one of exercise 06):

```sql
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT date_trunc('month', payment_date)::date AS month, sum(amount) AS revenue
FROM payment
GROUP BY 1;

CREATE UNIQUE INDEX ON monthly_revenue (month);
```

**Tasks.** Put the functions in `patterns.py` and the demonstrations in `demo.py`, which prints what happens at each step.

1. Recently viewed films. `record_view(customer_id, film_id)` adds the film to the sorted set `customer:{customer_id}:viewed` with the current time as score, keeps only the 20 most recent, and sets the key to expire 30 days after the last view. `recent_views(customer_id)` returns the film IDs, most recent first. Demonstration: customer 1 views films 1 to 25 in order; `recent_views(1)` returns films 25 down to 6; viewing film 10 again moves it to the front without duplicating it; `TTL` is close to 2,592,000 seconds.
2. Cache-aside. `get_film(film_id)` reads `cache:film:{film_id}` (JSON with `title`, `rating`, `length` and `rental_rate`); on a miss it reads PostgreSQL and stores the result for 300 seconds. `update_film_rate(film_id, rate)` updates PostgreSQL and deletes the cache key. Demonstration for film 1: the first `get_film` is a miss, the second a hit, then `update_film_rate(1, 1.99)`, and the next `get_film` is a miss that returns 1.99.
3. Lock. `refresh.py` takes the lock `lock:refresh:monthly_revenue` with `SET ... NX EX 60` and a random token, runs `REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_revenue`, waits 5 seconds while still holding the lock (so that the overlap is visible), and releases the lock with a Lua script that deletes it only if it still holds the token. Demonstration: start two processes at the same time (`uv run python refresh.py & uv run python refresh.py & wait`); one prints that it refreshed, the other that it skipped because the lock was held.
4. Rate limit. `allow_request(customer_id)` allows 10 requests per customer per minute, with a counter per customer per minute that expires. Demonstration: 12 calls in a row for customer 1 give 10 `True` and 2 `False`; after the next minute starts, a call gives `True` again.

**Deliverables.**

- `patterns.py`, `demo.py`, `refresh.py`, `pyproject.toml`.
- `README.md` with the commands, the output of `demo.py` and of the two `refresh.py` processes, and a table of every key pattern you use with its Redis type, TTL and purpose.

**Done when.** Every demonstration shows the expected result, and the lock is never released by a process that does not hold it.

### Challenge (optional)

Folder: `exercises/15-redis/challenge/`

**Goal.** Replace the fixed-window rate limit with a sliding window and prove the difference with a test.

**Starting point.** The `allow_request` function of the exercise above, and `uv add pytest`.

**Tasks.**

1. Change the fixed-window function so that it takes the current time as an argument, `allow_request_fixed(customer_id, now)`, so that tests control the clock.
2. Write `allow_request_sliding(customer_id, now)`: 10 requests in any 60-second window, stored in a sorted set with the request time as score. Implement it as a Lua script that removes old entries, counts, and adds the new request in one atomic step. Each member must be unique even when two requests have the same time.
3. Write a pytest test that sends 10 requests at seconds 59.0 to 59.9 of one minute and 10 more at seconds 0.0 to 0.9 of the next, and shows that the fixed window accepts all 20 while the sliding window accepts only 10.
4. Write a test that sends 30 requests from 10 threads at the same moment to the sliding window and checks that exactly 10 are accepted.

**Deliverables.**

- The rate limit module and `tests/test_rate_limit.py`.
- `README.md` with `uv run pytest -v` output and an explanation of why the check and the insert must be atomic.

**Done when.** Both tests pass and show 20 accepted by the fixed window, 10 by the sliding window, and exactly 10 under concurrency.

---

## Session 16: Redis II, source of truth, rebuild and persistence

### Theory

When an application uses several engines, each piece of data falls into one of three groups:

- **Source of truth**: the authoritative copy. If engines disagree, this one wins. Domain data (customers, orders, payments) lives in PostgreSQL.
- **Derived data**: a copy computed from the source, kept for speed (a cached page, a Redis set of the films a customer has rented, a MongoDB report). It can be deleted and rebuilt.
- **Ephemeral data**: data that exists only in one place and whose loss is acceptable (a rate-limit counter, a "recently viewed" list). Write down why losing it is acceptable.

Writing to two engines is not atomic. If PostgreSQL commits and the Redis write fails (network, crash), they disagree. The usual approach: write to the source of truth first, then update Redis. If Redis is wrong, it can be fixed by rebuilding or by a periodic **reconciliation** that compares the two and corrects Redis. Never the other way round.

**Rebuild**: a script that, after `FLUSHALL`, recreates all derived Redis data from PostgreSQL. Build into a temporary key and `RENAME` it at the end, so readers never see a half-built value. **Verify**: a script that compares Redis with PostgreSQL and exits with an error if they differ, so it can run in CI or on a schedule.

Redis **persistence**:

- **RDB**: periodic snapshot to disk. Compact and quick to load, but you lose changes since the last snapshot.
- **AOF** (append-only file): logs every write. With `appendfsync everysec` you lose at most about one second. Larger files, slower restart.
- Both together, or none if all data is derived or ephemeral.

**Memory limits**: `maxmemory` caps memory use. When it is reached, `maxmemory-policy` decides what happens: `allkeys-lru` evicts the least recently used keys (right for a cache), `noeviction` rejects writes (right for data you cannot lose silently).

**Atomic composite operations**:

- `MULTI` / `EXEC`: queue commands and run them together.
- `WATCH key`: optimistic locking. If the watched key changes before `EXEC`, the transaction is aborted and you retry.
- Lua scripts (`EVAL`): run logic with conditions inside Redis, atomically.

Pub/sub sends messages to subscribers that are connected at that moment. Messages are not stored, so a subscriber that is offline misses them.

### Tutorial

Rebuild one customer's "films rented" set from PostgreSQL:

```python
import os
import psycopg
import redis

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def rebuild_customer(pg, customer_id: int) -> None:
    key = f"customer:{customer_id}:films"
    tmp = key + ":rebuild"
    film_ids = [row[0] for row in pg.execute("""
        SELECT DISTINCT i.film_id
        FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
        WHERE r.customer_id = %s
    """, (customer_id,))]

    pipe = r.pipeline(transaction=True)
    pipe.delete(tmp)
    if film_ids:
        pipe.sadd(tmp, *film_ids)
        pipe.rename(tmp, key)
    else:
        pipe.delete(key)
    pipe.execute()


with psycopg.connect(os.environ["READONLY_DATABASE_URL"]) as pg:
    for (customer_id,) in pg.execute("SELECT customer_id FROM customer"):
        rebuild_customer(pg, customer_id)
```

Rebuilding customer by customer means one query each. Once it works, rewrite it to read all rentals in a single query and fill Redis with one pipeline.

Verify:

```python
import sys

errors = 0
with psycopg.connect(os.environ["READONLY_DATABASE_URL"]) as pg:
    rows = pg.execute("""
        SELECT r.customer_id, count(DISTINCT i.film_id)
        FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
        GROUP BY r.customer_id
    """)
    for customer_id, expected in rows:
        actual = r.scard(f"customer:{customer_id}:films")
        if actual != expected:
            print(f"customer {customer_id}: redis={actual} postgres={expected}", file=sys.stderr)
            errors += 1

sys.exit(1 if errors else 0)
```

Persistence settings (in `redis.conf` or as `command` arguments in `docker-compose.yml`):

```
appendonly yes
appendfsync everysec
maxmemory 256mb
maxmemory-policy noeviction
```

Optimistic locking with `WATCH`: change a customer's username only if the new one is free.

```python
def change_username(customer_id: int, old: str, new: str) -> bool:
    with r.pipeline() as pipe:
        while True:
            try:
                pipe.watch("usernames")
                if pipe.sismember("usernames", new):
                    pipe.unwatch()
                    return False
                pipe.multi()
                pipe.srem("usernames", old)
                pipe.sadd("usernames", new)
                pipe.hset(f"customer:{customer_id}", "username", new)
                pipe.execute()
                return True
            except redis.WatchError:
                continue
```

The same logic as a Lua script, in one round trip:

```python
change = r.register_script("""
if redis.call('SISMEMBER', KEYS[1], ARGV[2]) == 1 then return 0 end
redis.call('SREM', KEYS[1], ARGV[1])
redis.call('SADD', KEYS[1], ARGV[2])
redis.call('HSET', KEYS[2], 'username', ARGV[2])
return 1
""")
change(keys=["usernames", "customer:5"], args=["old_name", "new_name"])
```

### Exercise (individual)

Folder: `exercises/16-consistency/exercise/`

**Goal.** Treat Redis as derived data: rebuild it from PostgreSQL, verify it, and choose its persistence.

**Starting point.** A fresh copy of Pagila and a uv project:

```bash
./scripts/create-db.sh ex16 --pagila --reset
uv init --bare
uv add redis "psycopg[binary]"
```

Use Redis logical database 1 for this exercise (end `REDIS_URL` with `/1`), so that `FLUSHDB` there does not delete the keys of other exercises.

**Tasks.**

1. `rebuild.py` creates, for every customer with rentals, the set `customer:{customer_id}:categories` with the names of the categories of every film the customer has rented (a film can have several categories). It reads PostgreSQL with one query and writes Redis with one pipeline. Each set is built in a temporary key and renamed at the end, so that readers never see a half-built set. Expected: 997 sets (customers 647 and 978 have no rentals).
2. Run `FLUSHDB` on database 1, run `rebuild.py`, and count the keys with `SCAN` (not `KEYS`).
3. `verify.py` compares every set with PostgreSQL, size and members, and also reports any `customer:*:categories` key for a customer who should not have one. It prints every difference and exits with 1 if there is any, 0 otherwise. Show it exiting with 1 after `SREM customer:1:categories Action`, with 1 after `SADD customer:647:categories Fake`, and with 0 after running `rebuild.py` again.
4. Fill a table for every key pattern of exercises 15 and 16 (viewed films, film cache, lock, rate limit, categories) with: its class (source of truth, derived or ephemeral), what is lost if Redis loses it, and how it comes back.
5. Choose one configuration for the Redis instance (`appendonly`, `appendfsync`, `maxmemory`, `maxmemory-policy`) and justify it against the table of task 4. `maxmemory-policy` applies to the whole instance, not to one key, so explain the trade-off and when you would use two Redis instances instead. `docker-compose.redis-aof.yml` in this repository turns on AOF; read the warning in `sessions/16-redis-consistency/` before using it.

**Deliverables.**

- `rebuild.py`, `verify.py`, `pyproject.toml`.
- `README.md` with the commands, the output of tasks 2 and 3, the table of task 4, and the configuration and justification of task 5.

**Done when.** The rebuild creates 997 sets in one query and one pipeline, `verify.py` detects both changes and passes after the rebuild, and every choice in tasks 4 and 5 is justified.

### Challenge (optional)

Folder: `exercises/16-consistency/challenge/`

**Goal.** Keep Redis in sync with PostgreSQL without a full rebuild, even when the worker or Redis fails, using the transactional outbox pattern.

**Starting point.** The `ex16` database, the sets built by `rebuild.py` and the `verify.py` of the exercise above. Turn on AOF with `docker-compose.redis-aof.yml` (following the warning in `sessions/16-redis-consistency/`), then run `CONFIG SET appendfsync always` in `redis-cli`. In this challenge, always restart Redis with the same `-f` files and run that `CONFIG SET` again after each restart, before the worker writes. Add this table to `ex16`:

```sql
CREATE TABLE outbox (
    outbox_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id  integer NOT NULL,
    film_id      integer NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz
);
```

**Tasks.**

1. `rent.py` inserts N new rentals (the number is an argument) for random existing customers and copies. Each rental and its `outbox` row are inserted in the same PostgreSQL transaction.
2. `worker.py` loops: in one transaction it claims up to 50 unprocessed rows with `FOR UPDATE SKIP LOCKED`, adds the categories of each film to `customer:{customer_id}:categories`, sets `processed_at` and commits.
3. Run `rent.py 5000` while the worker runs. Kill the worker (`kill -9`) in the middle of a batch and start it again. Then stop Redis (`docker compose kill redis`) in the middle of a batch, start it again with AOF on and let the worker finish.
4. Run `verify.py` at the end.
5. Explain why processing the same outbox row twice is harmless here, and what you would need if it were not (for example an `INCR`). Explain also why the result depends on Redis persistence: what could be lost with RDB only, or with `appendfsync everysec`, and why the outbox alone would not bring it back.

**Deliverables.**

- `rent.py`, `worker.py`.
- `README.md` with the steps you ran, the worker log around both failures, the final output of `verify.py`, and the explanation of task 5.

**Done when.** After both failures, every outbox row is processed and `verify.py` exits with 0 without running `rebuild.py`.

---

## Session 17: Project integration and disaster day

### Theory

Before delivery, every engine must work together in the scenario's full flows, under load, and survive the loss of any one of them.

The concurrency tests prove that the business rules hold when many requests arrive at once. Run them against the integrated system (API plus all three engines), not only against SQL.

A runbook is only useful if someone can follow it under pressure without the person who wrote it. Disaster day tests exactly that. The trainer deletes the volume of one engine, chosen on the day, and the group restores it using only the runbook. The real RTO (time to restore) and real RPO (data lost) are recorded and count towards the "Security and Backup/Restore" part of the rubric. The result shows whether the backups are current, the scripts work on a clean volume, and the derived data can be rebuilt.

### Tutorial

Go through the delivery checklist in the project brief and mark what is missing.

Run the full concurrency test suite with the API running:

```bash
docker compose up -d
uv run pytest tests/concurrency -v
```

Rehearse the disaster before the trainer runs it. For each engine:

```bash
./scripts/backup.sh
docker compose stop mongo
docker compose rm -f mongo
docker volume rm <project>_mongo_data
docker compose up -d mongo
time ./scripts/restore.sh mongo
```

Then check the data with the verification steps from your runbook (row and document counts, a known query, the Redis verification script). Every time you have to do something the runbook does not say, add it to the runbook.

### Exercise (group)

Defined in the group project brief.

### Challenge (optional, individual)

Folder: `exercises/17-disaster/challenge/`

**Goal.** Rehearse the loss of a whole engine on your own machine and restore it using only a runbook.

**Starting point.** The databases of earlier exercises: `ex16` in PostgreSQL, `pagila_docs` in MongoDB and the category sets in Redis database 1. If you do not have them, create them with the starting points of exercises 13 and 16.

Deleting a volume deletes every database of that engine, including `pagila` and the databases of all the other exercises and session projects. Do this only after task 1, and reload what you need afterwards (`./scripts/load-pagila.sh`, `./scripts/create-db.sh ...`).

**Tasks.**

1. Write `runbook.md` before the drill: how to back up each engine (`pg_dump` of `ex16`, `mongodump` of `pagila_docs`; Redis holds only derived data and is rebuilt), how to restore each one, and how to verify each restore (row counts, document counts, `verify.py` of exercise 16). Take the backups.
2. Pick the engine at random:

   ```bash
   python3 -c "import random; print(random.choice(['postgres', 'mongo', 'redis']))"
   ```

3. Delete its volume and start it empty (replace `<engine>` with the result):

   ```bash
   docker compose stop <engine>
   docker compose rm -f <engine>
   docker volume rm databases-module_<engine>_data
   docker compose up -d <engine>
   ```

4. Restore it following only `runbook.md`, timing every step. Each time you need something the runbook does not say, write it down and add it to the runbook afterwards.
5. Repeat tasks 3 and 4 for the other two engines.

**Deliverables.** `runbook.md` (the version after the drill) and `README.md` with, for each engine: the restore time (real RTO), the data lost (real RPO), the verification output, and the steps that were missing from the runbook.

**Done when.** All three engines were restored and verified, and the final runbook contains every step you had to add.

---

## Session 18: Cross-group review and documentation

### Theory

Code review finds problems the author can no longer see. A useful database review checks:

- constraints that enforce the domain rules in the database, not only in code;
- indexes backed by evidence, and none created without a reason;
- every query parameterised, in SQL and MongoDB;
- roles with least privilege, and the application never connecting as superuser;
- no secrets in Git;
- a clear source of truth for each piece of data, and a working Redis rebuild;
- a runbook someone outside the group could follow.

A useful review issue states the problem, where it is (file and line), why it matters (what can go wrong), and a suggestion. "The code is messy" helps nobody. "`app/routes/search.py:42` builds the filter with an f-string from `request.query`; a value of `' OR 1=1 --` returns every row; use a bound parameter" can be fixed in five minutes.

Receiving a review: answer every issue. Fix it, or explain why you disagree. Close it with a link to the commit or pull request.

### Tutorial

Open an issue in the other group's repository using this structure:

```markdown
**Problem**
The cache key for a user profile has no TTL when written by the admin endpoint.

**Where**
`app/admin/users.py:58`

**Why it matters**
Profiles edited by an admin are cached forever, so later changes never show up and memory grows without limit.

**Suggestion**
Set the same TTL as `get_profile()` does, or call that function instead of writing the key directly.
```

Work through the checklist above one item at a time, and open one issue per problem.

For the issues you receive, create a branch per fix, reference the issue in the pull request (`Fixes #12`), and have another member review it before merging.

Complete the `README.md` (how to run, stack, ER diagram, source-of-truth table, main decisions, authors and contributions, AI usage) and every file in `docs/`.

### Exercise (group)

Defined in the group project brief.

### Challenge (optional, individual)

Folder: `exercises/18-review/challenge/`

**Goal.** Review database code and write issues that someone can fix without asking you questions.

**Starting point.** Save this code as `app.py` in your challenge folder, exactly as shown, so that line numbers match. You do not need to run it.

```python
import os

import psycopg
import redis
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()
pg = psycopg.connect("postgresql://postgres:postgres@localhost:5432/pagila")
r = redis.Redis(host="localhost", port=6379)
mongo = MongoClient(os.environ["MONGO_URL"])["pagila_docs"]


@app.get("/customers/search")
def search(name: str):
    return pg.execute(f"SELECT * FROM customer WHERE last_name = '{name}'").fetchall()


@app.post("/login")
def login(body: dict):
    user = mongo.users.find_one({"email": body["email"], "password": body["password"]})
    return {"ok": user is not None}


@app.get("/films/{film_id}")
def film(film_id: int):
    cached = r.get(f"film:{film_id}")
    if cached:
        return cached
    row = pg.execute("SELECT * FROM film WHERE film_id = %s", (film_id,)).fetchone()
    r.set(f"film:{film_id}", str(row))
    return row


@app.post("/rentals/{rental_id}/pay")
def pay(rental_id: int, amount: float):
    balance = pg.execute(
        "SELECT c.balance FROM customer c JOIN rental r USING (customer_id) WHERE r.rental_id = %s",
        (rental_id,),
    ).fetchone()[0]
    pg.execute(
        "UPDATE customer SET balance = %s WHERE customer_id = (SELECT customer_id FROM rental WHERE rental_id = %s)",
        (balance - amount, rental_id),
    )
    pg.commit()
    return {"balance": balance - amount}


@app.get("/admin/clear-cache")
def clear_cache():
    for key in r.keys("*"):
        r.delete(key)
    return {"ok": True}
```

**Tasks.**

1. Use the checklist in the theory of this session to find at least 8 problems in `app.py`. Look at security, concurrency, data types, caching and the use of each engine.
2. Write one issue per problem in `issues.md`, using the structure of the tutorial: **Problem**, **Where** (`app.py:<line>`), **Why it matters** (a concrete failure, not a general statement) and **Suggestion**.
3. Order the issues from most to least serious and justify the top 3.
4. Write `app_fixed.py` with the fixes for your top 3 issues.

**Deliverables.** `app.py`, `issues.md`, `app_fixed.py`.

**Done when.** `issues.md` has at least 8 issues, each with a correct line number and a concrete failure, and `app_fixed.py` fixes the top 3 without introducing new problems.

---

## Session 19: Delivery and technical discussion

### Theory

The technical discussion is not graded as a presentation. It checks that each student understands and can explain the whole project, in any of the three engines, including code written with AI help. The trainer chooses the engine each student is asked about, usually the one they contributed least to.

The questions follow the topics of the module: why a constraint or an index exists, what would happen with two simultaneous requests, what is lost if Redis disappears, how the backup is restored, why some data is embedded and other data referenced.

The answers feed the individual modifier of the project mark (between −4 and +2).

### Tutorial

Prepare a 10-minute demonstration of your scenario's technical focus, with reproducible evidence:

- Scenario A: the concurrency test running live, showing the rule holds.
- Scenario B: `FLUSHALL` and the Redis rebuild, followed by the verification script passing.
- Scenario C: `EXPLAIN (ANALYZE, BUFFERS)` before and after your indexes on the large tables, and the ranking under load.

Rehearse it from a clean clone of the `v1.0` tag, so nothing depends on your local state.

To prepare for the individual questions, each member explains to the others the parts they did not write, especially in the engine where they contributed least.

### Exercise (group)

Defined in the group project brief.

### Challenge (optional, individual)

Folder: `exercises/19-reproducibility/challenge/`

**Goal.** Check that your exercises can be run by someone else, from a clean clone, with only your documentation.

**Starting point.** Your fork with the exercises pushed, and a machine or a folder where the repository has never been run. If you use the same machine, stop the running containers and use a new folder; the Docker volumes are shared, so start with `./scripts/load-pagila.sh --reset` and recreate every database with `--reset`.

**Tasks.**

1. Clone your fork into the clean location.
2. Following only the root `README.md` and the `README.md` of each exercise folder, run exercises 04, 09, 12 and 16 from scratch, timing each one.
3. Write down every step you had to work out that is not documented: a missing command, a missing environment variable, a wrong path, a missing dependency. Each one is a documentation bug.
4. Fix every bug in the READMEs, push, and tag the commit `exercises-v1`.
5. Repeat tasks 1 and 2 from the tag and confirm that no step is missing.

**Deliverables.** `README.md` in the challenge folder with the times of task 2, the list of documentation bugs with the commit that fixed each one, and the times of the second run.

**Done when.** The second run from `exercises-v1` needs no step that is not written in the READMEs.

---

## Resources

Books:

- Silberschatz, Korth, Sudarshan: *Database System Concepts*
- Markus Winand: *SQL Performance Explained*, free web version at https://use-the-index-luke.com/
- Bradshaw, Brazil, Chodorow: *MongoDB: The Definitive Guide*

Documentation:

- PostgreSQL: https://www.postgresql.org/docs/
- MongoDB: https://www.mongodb.com/docs/
- Redis: https://redis.io/docs/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- Alembic: https://alembic.sqlalchemy.org/
- FastAPI: https://fastapi.tiangolo.com/

Sample data:

- Pagila: https://github.com/devrimgunduz/pagila

## Licence

GPL-3.0. See [LICENSE](LICENSE).
