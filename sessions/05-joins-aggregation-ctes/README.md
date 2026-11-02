# Session 05: Joins, aggregation and CTEs

The tutorial from [session 05](../../README.md#session-05-queries-i-joins-aggregation-subqueries-and-ctes), written three times as independent projects.

The tutorial's ten business questions on a copy of Pagila, one endpoint each: rentals per staff member, customers with more than 40 rentals, rentals per customer with `LEFT JOIN`, films with no copy in stock, customers who never rented, customers with the same name (self join), films longer than the average and than their rating's average (subquery and correlated subquery), rentals and payments per customer without the 1:N duplication, and customers above the average spend.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | The tutorial's SQL, returned with the rows | 8000 |
| [django](django/) | ORM and SQL versions (`?impl=orm|sql`), SQL shown | 8001 |
| [nextjs](nextjs/) | Prisma query API and `$queryRaw` (`?impl=orm|sql`), SQL logged | 3000 |

Look at the SQL each ORM generates for the same question and at which questions are easier to write in plain SQL.
