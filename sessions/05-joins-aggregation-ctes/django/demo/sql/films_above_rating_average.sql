-- Which films are longer than the average film with the same rating? (correlated subquery)
SELECT f.film_id, f.title, f.rating, f.length
FROM film f
WHERE f.length > (
    SELECT avg(f2.length) FROM film f2 WHERE f2.rating = f.rating
)
ORDER BY f.rating, f.length DESC, f.film_id;
