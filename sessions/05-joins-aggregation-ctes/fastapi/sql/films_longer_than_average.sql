-- Which films are longer than the average film?
-- Subquery in WHERE: it does not depend on the outer row, so it runs once and returns one value.
SELECT f.film_id, f.title, f.length
FROM film f
WHERE f.length > (SELECT avg(length) FROM film)
ORDER BY f.length DESC, f.film_id;
