-- Which customers spent more than the average customer? (CTE in steps)
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
