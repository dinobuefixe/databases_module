-- 60,000 random reviews, the same on every run (setseed).
SELECT setseed(0.18);

INSERT INTO film_review (customer_id, film_id, rating, body, created_at)
SELECT (random() * 998 + 1)::int,
       (random() * 999 + 1)::int,
       (random() * 4 + 1)::int,
       'Review ' || g,
       now() - random() * interval '2 years'
FROM generate_series(1, 60000) AS g
ON CONFLICT (customer_id, film_id) DO NOTHING;

ANALYZE film_review;
