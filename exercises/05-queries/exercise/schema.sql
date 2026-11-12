/*
1 - The number of films per category, including categories with no films, 
most films first, then by category name. Expected: 16 rows; 
the first two are Drama and Music, with 152 films each.
*/
SELECT c.name, COUNT(fc.film_id) AS film_count
FROM category c
LEFT JOIN film_category fc ON fc.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY film_count DESC, c.name;

/*
2 - Revenue per category per month in 2025, by payment_date. 
Expected: 192 rows; Action in January 2025 has 314.94.
*/
SELECT c.name AS category,
       date_trunc('month', p.payment_date) AS month,
       SUM(p.amount) AS revenue
FROM payment p
JOIN rental r       ON r.rental_id = p.rental_id
JOIN inventory i    ON i.inventory_id = r.inventory_id
JOIN film_category fc ON fc.film_id = i.film_id
JOIN category c     ON c.category_id = fc.category_id
WHERE p.payment_date >= '2025-01-01'
  AND p.payment_date <  '2026-01-01'
GROUP BY c.name, date_trunc('month', p.payment_date)
ORDER BY c.name, month;

/*
3 - Films that have never been rented, including films with 
no copy in any store. Expected: 42 rows.
*/
SELECT f.film_id, f.title
FROM film f
WHERE NOT EXISTS (
    SELECT 1
    FROM inventory i
    JOIN rental r ON r.inventory_id = i.inventory_id
    WHERE i.film_id = f.film_id
);

/*
4 - Customers who have rented films of all 5 
ratings. Expected: 908 rows.
*/
SELECT c.customer_id, c.first_name, c.last_name
FROM customer c
JOIN rental r       ON r.customer_id = c.customer_id
JOIN inventory i    ON i.inventory_id = r.inventory_id
JOIN film f         ON f.film_id = i.film_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING COUNT(DISTINCT f.rating) = (SELECT COUNT(DISTINCT rating) FROM film);

/*
5 - Pairs of actors who appeared together in more than 3 films, 
each pair listed once, with the number of films (self join).
 Expected: 143 rows.
*/
SELECT a1.actor_id, a1.first_name, a1.last_name,
       a2.actor_id, a2.first_name, a2.last_name,
       COUNT(*) AS film_count
FROM film_actor fa1
JOIN film_actor fa2 ON fa2.film_id = fa1.film_id
                   AND fa2.actor_id > fa1.actor_id
JOIN actor a1 ON a1.actor_id = fa1.actor_id
JOIN actor a2 ON a2.actor_id = fa2.actor_id
GROUP BY a1.actor_id, a1.first_name, a1.last_name,
         a2.actor_id, a2.first_name, a2.last_name
HAVING COUNT(*) > 3;

/*
6 - Countries with more than 20 customers, with the number of customers 
and the total they paid, most customers first. Expected: 7 rows; the first is Mexico 
with 430 customers.
*/
SELECT co.country,
       COUNT(*) AS customer_count,
       COALESCE(SUM(t.total_paid), 0) AS total_paid
FROM customer c
JOIN address a ON a.address_id = c.address_id
JOIN city ci   ON ci.city_id = a.city_id
JOIN country co ON co.country_id = ci.country_id
LEFT JOIN (
    SELECT customer_id, SUM(amount) AS total_paid
    FROM payment
    GROUP BY customer_id
) t ON t.customer_id = c.customer_id
GROUP BY co.country_id, co.country
HAVING COUNT(*) > 20
ORDER BY customer_count DESC;

/*
7 - Customers who paid more in total than the average customer 
of their own country. A customer with no payments counts as 0. 
 Expected: 449 rows.
*/
WITH customer_totals AS (
    SELECT c.customer_id, c.first_name, c.last_name,
           ci.country_id,
           COALESCE(SUM(p.amount), 0) AS total_paid
    FROM customer c
    JOIN address a ON a.address_id = c.address_id
    JOIN city ci   ON ci.city_id = a.city_id
    LEFT JOIN payment p ON p.customer_id = c.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, ci.country_id
),
country_avg AS (
    SELECT country_id, AVG(total_paid) AS avg_paid
    FROM customer_totals
    GROUP BY country_id
)
SELECT ct.customer_id, ct.first_name, ct.last_name, ct.total_paid, ca.avg_paid
FROM customer_totals ct
JOIN country_avg ca ON ca.country_id = ct.country_id
WHERE ct.total_paid > ca.avg_paid;

/*
8 - The longest films of each rating, including ties, using a subquery. 
Expected: 14 rows.
*/
SELECT f.film_id, f.title, f.rating, f.length
FROM film f
WHERE f.length = (
    SELECT MAX(f2.length)
    FROM film f2
    WHERE f2.rating = f.rating
);

/*
9 - Customers with no rental on or after 2026-04-01. 
Expected: 49 rows.
*/
SELECT c.customer_id, c.first_name, c.last_name
FROM customer c
WHERE NOT EXISTS (
    SELECT 1
    FROM rental r
    WHERE r.customer_id = c.customer_id
      AND r.rental_date >= '2026-04-01'
);

/*
10 - For each category, the average number of days a film stays out (return_date - rental_date, 
returned rentals only), rounded to 2 decimals, highest first. Expected: 16 rows; 
the first is Sci-Fi with 5.30.
*/
SELECT c.name AS category,
ROUND(AVG(EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 86400.0)::numeric, 2) AS avg_days_out
FROM rental r
JOIN inventory i      ON i.inventory_id = r.inventory_id
JOIN film_category fc ON fc.film_id = i.film_id
JOIN category c       ON c.category_id = fc.category_id
WHERE r.return_date IS NOT NULL
GROUP BY c.category_id, c.name
ORDER BY avg_days_out DESC;