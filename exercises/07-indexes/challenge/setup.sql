-- Challenge 07 - tabela grande para comparar paginacao
-- Correr numa base de dados vazia:
--   ./scripts/create-db.sh ch07 --reset
--   docker compose exec -T postgres psql -U postgres -d ch07 \
--       -v ON_ERROR_STOP=1 < exercises/07-indexes/challenge/setup.sql

SELECT setseed(0.1);

DROP TABLE IF EXISTS big_rental;

CREATE TABLE big_rental AS
SELECT g AS id,
       (random() * 599 + 1)::int                 AS customer_id,
       now() - random() * interval '3 years'      AS rented_at,
       CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
FROM generate_series(1, 2000000) AS g;

VACUUM ANALYZE big_rental;
