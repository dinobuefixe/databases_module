-- The incident: a DELETE without a proper WHERE.
BEGIN;
DELETE FROM payment WHERE payment_date >= '2026-01-01';
DELETE FROM film_actor WHERE actor_id <= 50;
DELETE FROM film_category WHERE category_id = 1;
COMMIT;
