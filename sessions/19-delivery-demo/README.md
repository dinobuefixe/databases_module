# Session 19: Delivery and demo

The tutorial from [session 19](../../README.md#session-19-delivery-and-technical-discussion), written three times as independent projects.

Each project is a demo-ready app with one command per piece of evidence for the technical discussion:

- concurrency: withdrawals with and without the fix, showing the rule broken and then holding (session 08);
- rebuild: Redis emptied, verification failing, rebuilt from PostgreSQL, verification passing (session 16);
- explain: `EXPLAIN (ANALYZE, BUFFERS)` before and after indexes on a 2,000,000-row table (session 07).

`scripts/clean-clone-check.sh` clones a repository at a tag into a temporary folder, follows the setup steps and reports how long it took. Each README is written as the guide for running the project from a clean clone.

| Project | Demo commands | Port |
|---------|---------------|------|
| [fastapi](fastapi/) | `make demo-concurrency`, `make demo-rebuild`, `make demo-explain` | 8000 |
| [django](django/) | management commands `demo_concurrency`, `demo_rebuild`, `demo_explain` | 8001 |
| [nextjs](nextjs/) | `npm run demo:concurrency`, `demo:rebuild`, `demo:explain` | 3000 |
