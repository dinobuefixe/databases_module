-- Running total of one customer's payments.
-- With ORDER BY inside OVER, SUM adds up every row from the start of the partition to this one.
SELECT customer_id, payment_date, amount,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY payment_date) AS running_total
FROM payment
WHERE customer_id = %(customer_id)s
ORDER BY customer_id, payment_date;
