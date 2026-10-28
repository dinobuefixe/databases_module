-- How many rentals has each customer made, and how much have they paid?
-- Joining rental and payment to customer in one go pairs every rental with every payment
-- of the same customer, so sum(amount) is multiplied by the number of rentals.
-- Subqueries in FROM aggregate each table first: one row per customer on each side.
SELECT c.customer_id, c.first_name, c.last_name,
       coalesce(r.rentals, 0) AS rentals,
       coalesce(p.paid, 0)    AS paid
FROM customer c
LEFT JOIN (
    SELECT customer_id, count(*) AS rentals FROM rental GROUP BY customer_id
) r ON r.customer_id = c.customer_id
LEFT JOIN (
    SELECT customer_id, sum(amount) AS paid FROM payment GROUP BY customer_id
) p ON p.customer_id = c.customer_id
ORDER BY c.customer_id;
