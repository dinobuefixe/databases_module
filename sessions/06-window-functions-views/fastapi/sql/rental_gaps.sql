-- Time between consecutive rentals of the same customer.
-- LAG reads rental_date from the previous row; the first rental has no previous row, so gap is NULL.
SELECT customer_id, rental_date,
       rental_date - LAG(rental_date) OVER (PARTITION BY customer_id ORDER BY rental_date) AS gap
FROM rental
WHERE customer_id = %(customer_id)s
ORDER BY rental_date;
