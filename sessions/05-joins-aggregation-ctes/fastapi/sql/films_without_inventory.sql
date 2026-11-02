-- Which films have no copy in any store?
-- Anti-join: keep the films for which the subquery finds no inventory row.
SELECT f.film_id, f.title
FROM film f
WHERE NOT EXISTS (
    SELECT 1 FROM inventory i WHERE i.film_id = f.film_id
);
