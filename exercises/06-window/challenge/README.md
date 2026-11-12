# Challenge 06 — "Gaps and islands" com window functions

**Objetivo.** Resolver um problema de *gaps and islands* com window functions.

Uma **ilha** é uma sequência de meses de calendário consecutivos em que um
cliente arrendou pelo menos um filme. Em Pagila, março e abril de 2022 não têm
arrendamentos nenhuns, por isso criam um "gap" para todos os clientes.

## Ficheiro

- `islands.sql` — a query única que devolve as 10 ilhas mais longas.

## Como correr

Na raiz do repositório:

```bash
./scripts/create-db.sh ch06 --pagila --reset
docker compose exec -T postgres psql -U postgres -d ch06 \
    -v ON_ERROR_STOP=1 < exercises/06-window/challenge/islands.sql
```

## Resultado

```
 customer_id | first_month | last_month | months
-------------+-------------+------------+--------
          70 | 2023-06     | 2024-12    |     19
         547 | 2022-05     | 2023-10    |     18
         567 | 2022-06     | 2023-11    |     18
          33 | 2023-07     | 2024-11    |     17
         158 | 2022-11     | 2024-03    |     17
         299 | 2022-05     | 2023-09    |     17
         443 | 2023-07     | 2024-11    |     17
         533 | 2023-04     | 2024-08    |     17
         740 | 2024-07     | 2025-11    |     17
         556 | 2023-09     | 2024-12    |     16
(10 rows)
```

A primeira linha é o cliente **70**, com **19 meses** de `2023-06` a `2024-12`;
a décima é o cliente **556**, com **16 meses** — exatamente como esperado.

## Técnica usada para agrupar meses consecutivos

O truque das ilhas está na CTE `numbered`:

```sql
month - (row_number() OVER (PARTITION BY customer_id ORDER BY month)
         * interval '1 month') AS island_key
```

1. `months` fica com **um mês por cliente** (`SELECT DISTINCT` de
   `date_trunc('month', rental_date)`), ou seja, só os meses em que houve
   arrendamento.
2. `row_number()` numera esses meses **de 1 a N, por cliente, por ordem
   crescente**.
3. A cada mês subtrai-se `n` meses, onde `n` é o número de ordem. Se os meses
   forem consecutivos, `mês − n` é sempre o mesmo valor: uma ilha recebe sempre
   a mesma `island_key`. Quando há um buraco (por exemplo, o salto de abril
   2022 para maio 2022 muda o número de ordem sem mudar o mês na mesma
   proporção), o valor da chave salta e começa uma **nova ilha**.

Depois basta agrupar por `(customer_id, island_key)`: `min(month)` é o primeiro
mês, `max(month)` o último e `count(*)` a duração.

Para escolher a ilha mais longa de cada cliente usa-se
`row_number() OVER (PARTITION BY customer_id ORDER BY months DESC, first_month)`
e fica-se com `rn = 1`: em caso de empate no comprimento, a ordem por
`first_month` garante que fica a ilha **mais antiga**. A ordenação final
(`months DESC, customer_id`) devolve as 10 mais longas, com empates desfeitos
pelo `customer_id`.

Tudo com window functions e agregações — sem `WITH RECURSIVE` e sem código
procedural.
