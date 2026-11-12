-- Challenge 06 - "gaps and islands": meses consecutivos com arrendamentos
--
-- Uma ilha e uma sequencia de meses de calendario consecutivos em que um
-- cliente arrendou pelo menos um filme. Em Pagila, marco e abril de 2022 nao
-- tem arrendamentos nenhuns.
--
-- So se usam window functions e operacoes de conjunto: sem codigo procedural
-- e sem CTE recursiva.
--
-- Correr numa copia do Pagila:
--   ./scripts/create-db.sh ch06 --pagila --reset
--   docker compose exec -T postgres psql -U postgres -d ch06 \
--       -v ON_ERROR_STOP=1 < exercises/06-window/challenge/islands.sql

WITH months AS (
    -- 1. Um mes (primeiro dia do mes) por cliente, sem repeticoes.
    SELECT DISTINCT
           customer_id,
           date_trunc('month', rental_date)::date AS month
    FROM rental
),
numbered AS (
    -- 2. Truque das ilhas: dentro de cada cliente, numerar os meses por ordem.
    --    Se os meses forem consecutivos, month - n meses e constante. Quando
    --    ha um buraco, o valor salta e comeca uma ilha nova.
    SELECT customer_id,
           month,
           month - (row_number() OVER (PARTITION BY customer_id ORDER BY month)
                    * interval '1 month') AS island_key
    FROM months
),
islands AS (
    -- 3. Cada island_key e uma ilha: primeiro mes, ultimo mes e duracao.
    SELECT customer_id,
           island_key,
           min(month) AS first_month,
           max(month) AS last_month,
           count(*)   AS months
    FROM numbered
    GROUP BY customer_id, island_key
),
longest AS (
    -- 4. A ilha mais longa de cada cliente; em empate, a mais antiga.
    SELECT customer_id, first_month, last_month, months,
           row_number() OVER (
               PARTITION BY customer_id
               ORDER BY months DESC, first_month ASC
           ) AS rn
    FROM islands
)
-- 5. Os 10 clientes com as ilhas mais longas; empate desfeito por customer_id.
SELECT customer_id, first_month, last_month, months
FROM longest
WHERE rn = 1
ORDER BY months DESC, customer_id
LIMIT 10;
