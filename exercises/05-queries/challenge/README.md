# Challenge 05 — Graus de separação com `WITH RECURSIVE`

**Objetivo.** Percorrer um grafo guardado em tabelas com uma CTE recursiva.

Dois atores estão **ligados** quando apareceram juntos em pelo menos 3 filmes.
A **distância** entre dois atores é o menor número de ligações entre eles.

## Ficheiro

- `degrees.sql` — a CTE `edge`, a query da tarefa 2 e a query da tarefa 3.

## Como correr

Na raiz do repositório:

```bash
./scripts/create-db.sh ch05 --pagila --reset
docker compose exec -T postgres psql -U postgres -d ch05 \
    -v ON_ERROR_STOP=1 < exercises/05-queries/challenge/degrees.sql
```

## Tarefa 1 — a CTE `edge`

```sql
edge AS (
    SELECT a1.actor_id, a2.actor_id AS other_actor_id
    FROM film_actor a1
    JOIN film_actor a2
      ON a2.film_id = a1.film_id
     AND a2.actor_id <> a1.actor_id
    GROUP BY a1.actor_id, a2.actor_id
    HAVING count(*) >= 3
)
```

A junção de `film_actor` consigo própria, por `film_id`, junta todos os pares de
atores que entram no mesmo filme; `count(*) >= 3` fica só com os pares que
partilham 3 ou mais filmes. Como cada par aparece nas duas ordenações
`(X, Y)` e `(Y, X)`, a CTE já tem **as duas direções**.

Resultado: **1.650 ligações** (arestas dirigidas) entre **199 atores**.

## Tarefa 2 — atores a menos de 3 graus do ator 1

```sql
walk AS (
    SELECT 1 AS actor_id, ARRAY[1] AS path, 0 AS distance
    UNION ALL
    SELECT e.other_actor_id, w.path || e.other_actor_id, w.distance + 1
    FROM walk w
    JOIN edge e ON e.actor_id = w.actor_id
    WHERE w.distance < 3
      AND NOT e.other_actor_id = ANY(w.path)
)
```

Número de atores a cada distância (o ator 1 não conta):

| distance | atores |
|---------:|-------:|
| 1 | 3 |
| 2 | 23 |
| 3 | 115 |

Primeiras linhas do resultado:

```
 actor_id | first_name |  last_name  | distance
----------+------------+-------------+----------
        4 | JENNIFER   | DAVIS       |        1
       20 | LUCILLE    | TRACY       |        1
       64 | RAY        | JOHANSSON   |        1
        7 | GRACE      | MOSTEL      |        2
       13 | UMA        | WOOD        |        2
```

A `min(distance)` na query exterior garante que cada ator aparece uma só vez,
com a sua distância **mais curta**, mesmo que a recursão o encontre por vários
caminhos.

## Tarefa 3 — caminho mais curto do ator 1 ao ator 200

```
 step | actor_id | first_name | last_name
------+----------+------------+-----------
    1 |        1 | PENELOPE   | GUINESS
    2 |       64 | RAY        | JOHANSSON
    3 |       65 | ANGELA     | HUDSON
    4 |       52 | CARMEN     | HUNT
    5 |      200 | THORA      | TEMPLE
```

O ator 200 está a **4 graus** (5 atores no caminho). A subquery escolhe o
caminho de menor `distance` e `unnest(...) WITH ORDINALITY` devolve os nomes
pela ordem do caminho. Se não existisse caminho em até 5 graus, a subquery
`best` ficava vazia e a query devolvia **0 linhas**.

## Porque é que a recursão não corre para sempre

1. **Limite de profundidade** — `WHERE w.distance < 3` (ou `< 5` na tarefa 3)
   impede a expansão a partir do momento em que se atinge o grau máximo
   pretendido.
2. **Sem ciclos no mesmo caminho** — `NOT e.other_actor_id = ANY(w.path)`
   verifica se o ator de destino já está no caminho atual antes de o acrescentar.
   A coluna `path` é um array que vai crescendo (`w.path || e.other_actor_id`),
   por isso a recursão nunca volta a um ator que já visitou nesse caminho e não
   entra em ciclo.
3. **`UNION ALL` com condição de paragem** — a parte recursiva só gera linhas
   enquanto houver arestas válidas e profundidade disponível; quando deixam de
   existir linhas novas, a CTE termina sozinha.

Sem a verificação do caminho, um par de atores ligado nos dois sentidos (A→B e
B→A) faria a recursão alternar entre os dois indefinidamente.
