# Session 18: review this project

This folder is the session 18 tutorial in Next.js. The app in it (described in `README.md`) was written for you to review, as you will review another group's project. Treat it as a pull request from a colleague: run it, read every file, and open one issue per problem you find, using `.github/ISSUE_TEMPLATE/review.md`.

Then practise the other side: pick one of your issues, create a branch for the fix, and open a pull request with `.github/pull_request_template.md` that says `Fixes #<issue number>`.

## Checklist

Go through it one item at a time. For each item, write down what you checked, even when you found nothing.

- [ ] **Constraints.** Every domain rule stated in the README or the code is enforced by the database (`CHECK`, `UNIQUE`, `NOT NULL`, foreign keys), not only by the API. Look at `prisma/schema.prisma` and every `migration.sql`.
- [ ] **Indexes with evidence.** Each frequent query has an index that matches it, backed by `EXPLAIN (ANALYZE, BUFFERS)` before and after. No index exists without a query that needs it.
- [ ] **Parameterised queries.** Every SQL statement and every MongoDB filter receives user input as a parameter, never pasted into the query text. Search the code for raw SQL and for queries built from strings.
- [ ] **Least privilege.** The app connects with a role that can only do what the app needs. It never connects as the superuser or the owner of the schema.
- [ ] **No secrets in Git.** No passwords, keys or connection strings with credentials in committed files, including default values in code.
- [ ] **Source of truth and Redis rebuild.** For every Redis key: is it derived, ephemeral or the only copy? Does every write path keep it correct, with the same TTL? Is there a script that rebuilds it after `FLUSHALL`, and one that verifies it?
- [ ] **Runbook.** Someone outside the group could back up and restore every engine by following the docs alone.
- [ ] **README and docs.** How to run, stack, ER diagram, source-of-truth table, main decisions, authors and contributions, AI usage. Every file in `docs/` is complete.

## A useful issue

States the problem, where it is (file and line), why it matters (what can go wrong) and a suggestion. "The code is messy" helps nobody.
