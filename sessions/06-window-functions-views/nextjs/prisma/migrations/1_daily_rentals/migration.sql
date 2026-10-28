-- Written by hand: Prisma's schema cannot describe a materialised view.

-- Rentals per day, stored. Fast to read, stale until refreshed.
CREATE MATERIALIZED VIEW daily_rentals AS
SELECT rental_date::date AS day, count(*) AS rentals
FROM rental
GROUP BY 1;

-- REFRESH ... CONCURRENTLY needs a unique index on the materialised view.
CREATE UNIQUE INDEX daily_rentals_day ON daily_rentals (day);
