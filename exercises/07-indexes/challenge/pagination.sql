-- Challenge 07 - OFFSET vs keyset pagination, e Index Only Scan vs VACUUM
--
-- Requer a tabela big_rental criada por setup.sql:
--   ./scripts/create-db.sh ch07 --reset
--   docker compose exec -T postgres psql -U postgres -d ch07 \
--       -v ON_ERROR_STOP=1 < exercises/07-indexes/challenge/setup.sql
--   docker compose exec -T postgres psql -U postgres -d ch07 \
--       -v ON_ERROR_STOP=1 < exercises/07-indexes/challenge/pagination.sql
--
-- As paginas sao de 20 linhas da tabela inteira, ordenada por
-- rented_at DESC, id DESC. A pagina 5.000 comeca depois de 99.980 linhas.

\timing on

-- 1. Indice que corresponde exatamente a ordenacao (e, mais tarde, as
--    colunas devolvidas pela query de keyset).
CREATE INDEX big_rental_rented_id
    ON big_rental (rented_at DESC, id DESC);
ANALYZE big_rental;

-- 2. Pagina 5.000 com OFFSET: a base de dados tem de produzir e descartar
--    99.980 linhas antes de devolver 20.
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, rented_at, customer_id
FROM big_rental
ORDER BY rented_at DESC, id DESC
OFFSET 99980 LIMIT 20;

-- 3. A mesma pagina com keyset pagination. Guarda-se a ultima linha da
--    pagina 4.999 (offset 99.979) em variaveis do psql...
SELECT rented_at AS last_rented_at, id AS last_id
FROM big_rental
ORDER BY rented_at DESC, id DESC
OFFSET 99979 LIMIT 1
\gset

-- ... e usa-se a comparacao de tuplos para saltar diretamente para a pagina.
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, rented_at, customer_id
FROM big_rental
WHERE (rented_at, id) < (:'last_rented_at', :last_id)
ORDER BY rented_at DESC, id DESC
LIMIT 20;

-- 4. Recriar o indice com INCLUDE (customer_id) para cobrir todas as colunas
--    devolvidas: a query passa a ser um Index Only Scan.
DROP INDEX big_rental_rented_id;
CREATE INDEX big_rental_rented_id
    ON big_rental (rented_at DESC, id DESC) INCLUDE (customer_id);
VACUUM ANALYZE big_rental;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, rented_at, customer_id
FROM big_rental
WHERE (rented_at, id) < (:'last_rented_at', :last_id)
ORDER BY rented_at DESC, id DESC
LIMIT 20;

-- 5. Visibilidade: um UPDATE reescreve ~1/50 das linhas e invalida o mapa de
--    visibilidade. O Index Only Scan passa a ter de ir ao heap ("Heap
--    Fetches"). O VACUUM volta a marcar as paginas como visiveis.
UPDATE big_rental SET customer_id = customer_id WHERE id % 50 = 0;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, rented_at, customer_id
FROM big_rental
WHERE (rented_at, id) < (:'last_rented_at', :last_id)
ORDER BY rented_at DESC, id DESC
LIMIT 20;

VACUUM big_rental;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, rented_at, customer_id
FROM big_rental
WHERE (rented_at, id) < (:'last_rented_at', :last_id)
ORDER BY rented_at DESC, id DESC
LIMIT 20;
