-- Which customers share their first and last name with another customer? (self join)
SELECT c1.customer_id, c2.customer_id AS other_customer_id, c1.first_name, c1.last_name
FROM customer c1
JOIN customer c2
  ON  c2.first_name  = c1.first_name
  AND c2.last_name   = c1.last_name
  AND c2.customer_id > c1.customer_id
ORDER BY c1.last_name, c1.first_name, c1.customer_id, other_customer_id;
