-- The N longest films per rating, with ties.
-- DENSE_RANK gives tied films the same position and leaves no gap after them.
-- A window function cannot go in WHERE, so the ranking happens in a CTE and the filter outside.
WITH ranked AS (
    SELECT title, rating, length,
           DENSE_RANK() OVER (PARTITION BY rating ORDER BY length DESC) AS pos
    FROM film
)
SELECT * FROM ranked WHERE pos <= %(top)s ORDER BY rating, pos;
