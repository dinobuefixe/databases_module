-- Which customers have never rented a film? (anti-join with LEFT JOIN)
SELECT c.customer_id, c.first_name, c.last_name
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
WHERE r.rental_id IS NULL
ORDER BY c.customer_id;
