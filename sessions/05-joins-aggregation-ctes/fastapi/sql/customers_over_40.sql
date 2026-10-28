-- Which customers rented more than 40 films?
-- WHERE would filter rentals before grouping; HAVING filters the groups after counting.
SELECT c.customer_id, c.first_name, c.last_name, count(*) AS rentals
FROM customer c
JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
HAVING count(*) > %(min_rentals)s
ORDER BY rentals DESC;
