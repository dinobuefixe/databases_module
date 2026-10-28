# Review checklist

Work through one item at a time. For every problem, open one issue with the template in `.github/ISSUE_TEMPLATE/review.md`: Problem, Where (file and line), Why it matters, Suggestion.

## Constraints

- [ ] Every rule the README or the code states about the data is enforced by the database (`CHECK`, `UNIQUE`, `NOT NULL`, foreign keys), not only by Python validators or forms.
- [ ] Read the migrations and run `\d <table>` in `psql`: what is in the database may differ from what the model suggests.

## Indexes

- [ ] Every index has a reason: a query that uses it, with `EXPLAIN (ANALYZE, BUFFERS)` before and after.
- [ ] Every frequent query that filters or sorts on a column has an index, or a note explaining why it does not need one.
- [ ] No index that no query uses (each one slows every write).

## Queries

- [ ] Every SQL statement sends user input as a bound parameter, never through an f-string, `%` or `+`.
- [ ] Every MongoDB filter is built by the code from validated values, never taken as it arrives in the request body.

## Roles and secrets

- [ ] The application connects with a role that has only the privileges it needs, never as `postgres` or another superuser.
- [ ] No password, key or connection string with a password in the code or in any committed file; `.env` is git-ignored.

## Source of truth and Redis

- [ ] For every piece of data, it is clear which engine is the source of truth.
- [ ] Every key in Redis has a documented TTL, or a reason for not having one, and every writer uses the same TTL.
- [ ] Derived data in Redis can be rebuilt from PostgreSQL with a script, and a verification script checks it.

## Documentation

- [ ] The README covers: how to run, stack, ER diagram, source-of-truth table, main decisions, authors and contributions, AI usage.
- [ ] A runbook in `docs/` that someone outside the group could follow to restore each engine.
