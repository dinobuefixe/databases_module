-- How many rentals has each customer made, including customers with none? (LEFT JOIN, count(*) vs count(column))
SELECT c.customer_id, c.first_name, c.last_name,
       count(r.rental_id) AS rentals,
       count(*)           AS joined_rows
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY rentals, c.customer_id;
