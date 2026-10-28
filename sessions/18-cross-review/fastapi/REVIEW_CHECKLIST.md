# Review checklist

Go through the items one at a time. For each problem you find, open one issue with the **Review issue** template (Problem / Where / Why it matters / Suggestion). One issue per problem, with the file and line.

## 1. Constraints enforce the domain rules in the database

- List the rules the README states. For each one, find the constraint (`CHECK`, `UNIQUE`, `NOT NULL`, foreign key, `EXCLUDE`) that enforces it in the schema.
- A rule checked only in Python or Pydantic does not count: a script, a migration or another service can still write a row that breaks it. Try the bad row directly in `psql`.

## 2. Indexes are backed by evidence

- For each frequent query (look at the endpoints), check with `EXPLAIN (ANALYZE, BUFFERS)` whether it reads the table with a `Seq Scan` on a large table.
- For each index in the schema, find the query that uses it and the evidence (an `EXPLAIN` before and after, a measured time). An index nobody can justify still costs space and write time.

## 3. Every query is parameterised

- Search for f-strings, `%` formatting, `+` concatenation or `.format()` near `text(`, `execute(`, `find(`.
- Values from the request must travel as bound parameters (`:name` with a dict in SQLAlchemy, `%s` in psycopg) or, in MongoDB, as validated values of the expected type.

## 4. Least privilege

- Which role does the application use to connect? Look at `.env.example` and the configuration code.
- The application must not connect as a superuser or as the owner of the schema. It needs `SELECT`, `INSERT`, `UPDATE`, `DELETE` on its tables, nothing more.

## 5. No secrets in Git

- Search the code and every committed file for passwords, tokens and keys, including default values in `os.getenv(..., "default")`.
- `.env` must be in `.gitignore`; `.env.example` holds only placeholders.
- A secret that was ever committed must be rotated, even if a later commit removed it.

## 6. Source of truth and Redis rebuild

- For each piece of data in Redis: where is the source of truth, and how is it rebuilt after `FLUSHALL`?
- Every write path for a cached value must behave the same way: same key, same TTL, same invalidation. Compare each place that writes a key with the function that reads it.

## 7. A runbook someone outside the group could follow

- Is there a restore runbook in `docs/`? Follow it without asking the authors. Every step you have to guess is an issue.
- Does the README cover how to run, stack, ER diagram, source-of-truth table, main decisions, authors and contributions, and AI usage?
