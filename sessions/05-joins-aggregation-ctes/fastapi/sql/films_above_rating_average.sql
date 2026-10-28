-- Which films are longer than the average film with the same rating?
-- Correlated subquery: f2.rating = f.rating refers to the outer row, so the average
-- is computed for the rating of each film.
SELECT f.film_id, f.title, f.rating, f.length
FROM film f
WHERE f.length > (
    SELECT avg(f2.length) FROM film f2 WHERE f2.rating = f.rating
)
ORDER BY f.rating, f.length DESC, f.film_id;
