-- Which customers have never rented a film?
-- Anti-join with LEFT JOIN: keep the customers for which the join found no rental.
SELECT c.customer_id, c.first_name, c.last_name
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
WHERE r.rental_id IS NULL
ORDER BY c.customer_id;
