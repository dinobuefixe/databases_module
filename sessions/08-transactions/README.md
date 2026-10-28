# Session 08: Transactions and concurrency

The tutorial from [session 08](../../README.md#session-08-transactions-and-concurrency), written three times as independent projects.

The tutorial's `account` table and three ways to withdraw money: a naive read-then-write that loses updates, an atomic conditional `UPDATE`, and a row lock. A script fires concurrent withdrawals at the API to show which strategies keep the balance correct, and another provokes a deadlock and fixes it with a fixed lock order.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `psycopg` transactions, `FOR UPDATE` | 8000 |
| [django](django/) | `transaction.atomic`, `F()`, `select_for_update()` | 8001 |
| [nextjs](nextjs/) | interactive `$transaction`, `updateMany` with a condition, `FOR UPDATE` in SQL | 3000 |

Run the concurrency script several times: the naive strategy gives a different wrong answer each time, the other two always give the same right one.
