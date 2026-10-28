-- Which customers rented more than 40 films? (HAVING)
SELECT c.customer_id, c.first_name, c.last_name, count(*) AS rentals
FROM customer c
JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
HAVING count(*) > 40
ORDER BY rentals DESC;
