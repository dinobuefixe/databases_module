-- Which films are longer than the average film? (subquery in WHERE)
SELECT f.film_id, f.title, f.length
FROM film f
WHERE f.length > (SELECT avg(length) FROM film)
ORDER BY f.length DESC, f.film_id;
