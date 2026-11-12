-- Challenge 05 - graus de separacao entre atores, com WITH RECURSIVE
--
-- Dois atores estao ligados quando apareceram juntos em pelo menos 3 filmes.
-- A distancia entre dois atores e o menor numero de ligacoes entre eles.
--
-- Correr numa copia do Pagila:
--   ./scripts/create-db.sh ch05 --pagila
--   docker compose exec -T postgres psql -U postgres -d ch05 \
--       -v ON_ERROR_STOP=1 < exercises/05-queries/challenge/degrees.sql

-- ---------------------------------------------------------------------------
-- 1. CTE edge(actor_id, other_actor_id) com todos os pares ligados, nos dois
--    sentidos. Um par (X, Y) aparece como (X, Y) e como (Y, X) porque a
--    juncao film_actor consigo propria gera as duas ordenacoes.
-- ---------------------------------------------------------------------------
WITH edge AS (
    SELECT a1.actor_id, a2.actor_id AS other_actor_id
    FROM film_actor a1
    JOIN film_actor a2
      ON a2.film_id = a1.film_id
     AND a2.actor_id <> a1.actor_id
    GROUP BY a1.actor_id, a2.actor_id
    HAVING count(*) >= 3
)
SELECT count(*) AS edges, count(DISTINCT actor_id) AS actors_with_edges
FROM edge;

-- ---------------------------------------------------------------------------
-- 2. Todos os atores alcancaveis a partir do ator 1 em ate 3 graus.
--    - A recursao para quando distance chega a 3 (WHERE w.distance < 3).
--    - "NOT other_actor_id = ANY(path)" impede revisitar um ator no mesmo
--      caminho, por isso a recursao nunca entra em ciclo.
--    - min(distance) da a distancia mais curta para cada ator.
-- ---------------------------------------------------------------------------
WITH RECURSIVE
edge AS (
    SELECT a1.actor_id, a2.actor_id AS other_actor_id
    FROM film_actor a1
    JOIN film_actor a2
      ON a2.film_id = a1.film_id
     AND a2.actor_id <> a1.actor_id
    GROUP BY a1.actor_id, a2.actor_id
    HAVING count(*) >= 3
),
walk AS (
    SELECT 1 AS actor_id, ARRAY[1] AS path, 0 AS distance
    UNION ALL
    SELECT e.other_actor_id, w.path || e.other_actor_id, w.distance + 1
    FROM walk w
    JOIN edge e ON e.actor_id = w.actor_id
    WHERE w.distance < 3
      AND NOT e.other_actor_id = ANY(w.path)
)
SELECT a.actor_id, a.first_name, a.last_name, min(w.distance) AS distance
FROM walk w
JOIN actor a ON a.actor_id = w.actor_id
WHERE w.distance > 0
GROUP BY a.actor_id, a.first_name, a.last_name
ORDER BY distance, a.actor_id;

-- Numero de atores a cada distancia (evidencia para o README).
WITH RECURSIVE
edge AS (
    SELECT a1.actor_id, a2.actor_id AS other_actor_id
    FROM film_actor a1
    JOIN film_actor a2
      ON a2.film_id = a1.film_id
     AND a2.actor_id <> a1.actor_id
    GROUP BY a1.actor_id, a2.actor_id
    HAVING count(*) >= 3
),
walk AS (
    SELECT 1 AS actor_id, ARRAY[1] AS path, 0 AS distance
    UNION ALL
    SELECT e.other_actor_id, w.path || e.other_actor_id, w.distance + 1
    FROM walk w
    JOIN edge e ON e.actor_id = w.actor_id
    WHERE w.distance < 3
      AND NOT e.other_actor_id = ANY(w.path)
)
SELECT distance, count(*) AS actors
FROM (
    SELECT actor_id, min(distance) AS distance
    FROM walk
    WHERE distance > 0
    GROUP BY actor_id
) d
GROUP BY distance
ORDER BY distance;

-- ---------------------------------------------------------------------------
-- 3. Caminho mais curto do ator 1 ao ator 200, como lista de nomes.
--    Se nao houver caminho em ate 5 graus, o resultado fica vazio (0 linhas).
-- ---------------------------------------------------------------------------
WITH RECURSIVE
edge AS (
    SELECT a1.actor_id, a2.actor_id AS other_actor_id
    FROM film_actor a1
    JOIN film_actor a2
      ON a2.film_id = a1.film_id
     AND a2.actor_id <> a1.actor_id
    GROUP BY a1.actor_id, a2.actor_id
    HAVING count(*) >= 3
),
walk AS (
    SELECT 1 AS actor_id, ARRAY[1] AS path, 0 AS distance
    UNION ALL
    SELECT e.other_actor_id, w.path || e.other_actor_id, w.distance + 1
    FROM walk w
    JOIN edge e ON e.actor_id = w.actor_id
    WHERE w.distance < 5
      AND NOT e.other_actor_id = ANY(w.path)
)
SELECT p.ord AS step, a.actor_id, a.first_name, a.last_name
FROM (
    SELECT w.path
    FROM walk w
    WHERE w.actor_id = 200
    ORDER BY w.distance
    LIMIT 1
) best
CROSS JOIN LATERAL unnest(best.path) WITH ORDINALITY AS p(actor_id, ord)
JOIN actor a ON a.actor_id = p.actor_id
ORDER BY p.ord;
