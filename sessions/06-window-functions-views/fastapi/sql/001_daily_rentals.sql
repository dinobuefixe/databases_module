-- Rentals per day, stored. Fast to read, stale until refreshed.
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_rentals AS
SELECT rental_date::date AS day, count(*) AS rentals
FROM rental
GROUP BY 1;

-- REFRESH ... CONCURRENTLY needs a unique index to match old and new rows.
CREATE UNIQUE INDEX IF NOT EXISTS daily_rentals_day ON daily_rentals (day);
