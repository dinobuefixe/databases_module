-- How many rentals has each customer made, including customers with none?
-- LEFT JOIN keeps every customer. A customer with no rentals gets one row with NULLs on the
-- rental side: count(r.rental_id) skips the NULL and gives 0, count(*) counts the row and gives 1.
SELECT c.customer_id, c.first_name, c.last_name,
       count(r.rental_id) AS rentals,
       count(*)           AS joined_rows
FROM customer c
LEFT JOIN rental r ON r.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY rentals, c.customer_id;
