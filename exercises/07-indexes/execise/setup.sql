SELECT setseed(0.1);
CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, 2000000) AS g;