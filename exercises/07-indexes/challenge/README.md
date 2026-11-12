# Challenge 07 — `OFFSET` vs keyset pagination, e `Index Only Scan` vs `VACUUM`

**Objetivo.** Comparar a paginação com `OFFSET` com a paginação por *keyset* e
ligar os `Index Only Scan` ao `VACUUM`.

A tabela `big_rental` tem 2.000.000 linhas. As páginas são de **20 linhas** de
toda a tabela, ordenada por `rented_at DESC, id DESC`. A página 5.000 começa
depois de 99.980 linhas (offsets 99.980 a 99.999).

## Ficheiros

- `setup.sql` — cria `big_rental` (2.000.000 linhas) e faz `VACUUM ANALYZE`.
- `pagination.sql` — todas as instruções das tarefas 1 a 5, por ordem.

## Como correr

```bash
./scripts/create-db.sh ch07 --reset
docker compose exec -T postgres psql -U postgres -d ch07 \
    -v ON_ERROR_STOP=1 < exercises/07-indexes/challenge/setup.sql
docker compose exec -T postgres psql -U postgres -d ch07 \
    -v ON_ERROR_STOP=1 < exercises/07-indexes/challenge/pagination.sql
```

## Tarefa 1 — índice que corresponde à ordenação

```sql
CREATE INDEX big_rental_rented_id
    ON big_rental (rented_at DESC, id DESC);
```

## Tarefa 2 — página 5.000 com `OFFSET`

```sql
SELECT id, rented_at, customer_id
FROM big_rental
ORDER BY rented_at DESC, id DESC
OFFSET 99980 LIMIT 20;
```

Plano (`EXPLAIN (ANALYZE, BUFFERS)`):

```
 Limit  (cost=5584.88..5586.00 rows=20 width=16) (actual time=255.723..255.738 rows=20.00 loops=1)
   Buffers: shared hit=87264 read=13113 written=7395
   ->  Index Scan using big_rental_rented_id on big_rental
         (cost=0.43..111711.79 rows=2000000 width=16)
         (actual time=0.051..251.293 rows=100000.00 loops=1)
```

**Tempo: ~256 ms.** Repare em `rows=100000`: o índice é percorrido 100.000
vezes (99.980 descartadas + 20 devolvidas) e quase todas essas linhas são
lidas do *heap*.

## Tarefa 3 — a mesma página com keyset

```sql
-- ultima linha da pagina 4.999
SELECT rented_at AS last_rented_at, id AS last_id
FROM big_rental ORDER BY rented_at DESC, id DESC OFFSET 99979 LIMIT 1
\gset

SELECT id, rented_at, customer_id
FROM big_rental
WHERE (rented_at, id) < (:'last_rented_at', :last_id)
ORDER BY rented_at DESC, id DESC LIMIT 20;
```

Plano:

```
 Limit  (cost=0.43..1.62 rows=20 width=16) (actual time=0.023..0.039 rows=20.00 loops=1)
   Buffers: shared hit=22 read=1
   ->  Index Scan using big_rental_rented_id on big_rental
         Index Cond: (ROW(rented_at, id) < ROW('2026-09-18 22:14:48.658832+00'::timestamptz, 13584))
         (actual time=0.022..0.037 rows=20.00 loops=1)
```

**Tempo: ~0,09 ms**, `rows=20`. A comparação de tuplos
`(rented_at, id) < (last_rented_at, last_id)` é usada diretamente pelo índice
como `Index Cond`, por isso o motor salta para a posição certa sem percorrer as
99.980 linhas anteriores.

**As duas queries devolvem as mesmas 20 linhas** (verificado com `EXCEPT`):

```
 offset_rows | keyset_rows | only_offset | only_keyset
-------------+-------------+-------------+-------------
          20 |          20 |           0 |           0
```

## Tarefa 4 — `Index Only Scan` com `INCLUDE`

```sql
DROP INDEX big_rental_rented_id;
CREATE INDEX big_rental_rented_id
    ON big_rental (rented_at DESC, id DESC) INCLUDE (customer_id);
VACUUM ANALYZE big_rental;
```

Plano da query de keyset:

```
 Limit  (cost=0.43..1.09 rows=20 width=16) (actual time=0.055..0.060 rows=20.00 loops=1)
   Buffers: shared hit=1 read=3
   ->  Index Only Scan using big_rental_rented_id on big_rental
         (cost=0.43..62448.26 rows=1898962 width=16) (actual time=0.054..0.057 rows=20.00 loops=1)
         Heap Fetches: 0
```

**Index Only Scan**, `Heap Fetches: 0`, **~0,08 ms**. Como o índice agora
contém `customer_id`, todas as colunas que a query precisa estão no próprio
índice e não é preciso ir ao *heap*.

## Tarefa 5 — visibilidade e `VACUUM`

```sql
UPDATE big_rental SET customer_id = customer_id WHERE id % 50 = 0;  -- 40000 linhas
```

Plano da query de keyset logo a seguir ao `UPDATE`:

```
 ->  Index Only Scan using big_rental_rented_id on big_rental
       (actual time=0.027..0.130 rows=20.00 loops=1)
       Heap Fetches: 20
```

**`Heap Fetches: 20`**, **~0,15 ms**. Depois:

```sql
VACUUM big_rental;
```

Plano da mesma query:

```
 ->  Index Only Scan using big_rental_rented_id on big_rental
       (actual time=0.031..0.034 rows=20.00 loops=1)
       Heap Fetches: 0
```

**`Heap Fetches: 0`**, **~0,05 ms**.

## Porque é que o `OFFSET` fica mais lento

`OFFSET n` obriga o motor a **produzir e descartar as primeiras n linhas** da
ordenação antes de devolver as seguintes. Mesmo com o índice a fornecer a
ordem, percorre as 99.980 linhas anteriores e, para cada uma, tem de confirmar
a visibilidade — ou seja, o custo cresce **linearmente com o número da
página**. A página 5.000 custa ~256 ms; a página 50.000 custaria cerca de 10
vezes mais. A paginação por keyset não tem `OFFSET`: usa o último valor já
visto como ponto de partida (`Index Cond`), por isso o custo é **constante**
(~0,1 ms) em qualquer página. O preço é não se poder saltar diretamente para
uma página arbitrária.

## O que o `VACUUM` muda no mapa de visibilidade

O `Index Only Scan` só pode responder só com o índice se, para cada linha,
souber que ela é visível **sem consultar o heap**. Para isso usa o **mapa de
visibilidade** (*visibility map*), um bit por página que diz se todos os
tuplos dessa página são visíveis a todas as transações.

O `UPDATE`, mesmo escrevendo o mesmo valor, cria **novas versões** das 40.000
linhas (`id % 50 = 0`): as antigas ficam mortas e as páginas deixam de estar
marcadas como totalmente visíveis no mapa. Como os primeiros 20 tuplos da
página 5.000 incluem linhas reescritas, o motor já não confia no mapa e vai ao
heap confirmar cada uma — daí `Heap Fetches: 20`.

O `VACUUM` remove as versões mortas e **volta a marcar essas páginas como
visíveis** no mapa de visibilidade. A partir daí o `Index Only Scan` responde
só com o índice e `Heap Fetches` volta a **0**.
