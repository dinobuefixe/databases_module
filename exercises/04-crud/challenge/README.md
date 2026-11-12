# Challenge 04 — gerar 1.000.000 de alugueres com `COPY`

**Objetivo.** Gerar um conjunto de dados grande, válido e reprodutível o mais
depressa possível. O script `seed.py` acrescenta 1.000.000 de linhas à tabela
`rental` do Pagila com `COPY`, a partir de dois `rental_id` fixos (100.001 a
1.100.000), de forma que duas bases diferentes fiquem com exatamente as mesmas
linhas novas.

## Ficheiros

- `seed.py` — carrega as 1.000.000 de linhas. O nome da base de dados é o
  argumento da linha de comandos.
- `pyproject.toml` — projeto `uv` com `faker` e `psycopg[binary]`.

## Como correr

```bash
./scripts/create-db.sh ch04_a --pagila --reset
./scripts/create-db.sh ch04_b --pagila --reset

cd exercises/04-crud/challenge
uv run python seed.py ch04_a
uv run python seed.py ch04_b
```

O script lê `DATABASE_URL` (do `.env`) e troca apenas o nome da base de dados
pelo argumento; sem essa variável usa o valor por omissão do módulo.

## Tarefa 1 — o que o `seed.py` garante

- **`rental_id` explícito** de 100.001 a 1.100.000. Como os ids são fixos, as
  duas bases ficam com as mesmas chaves. No fim a sequência é avançada com
  `setval(..., 1100000, true)`.
- **Chaves estrangeiras válidas**: cada `inventory_id`, `customer_id` e
  `staff_id` é escolhido a partir dos ids que existem mesmo em Pagila.
- **Datas válidas**: `rental_date` está entre `2022-01-01` e
  `2026-07-31 23:59:59.999999`; `return_date` é `NULL` (5% das linhas) ou
  posterior a `rental_date` (entre 1 hora e 30 dias depois).
- **Índice único respeitado**: o Pagila tem
  `UNIQUE (rental_date, inventory_id, customer_id)`. O script gera cada
  `rental_date` com um microssegundo distinto (`rng.sample` sobre todo o
  intervalo), por isso nenhum triplo se pode repetir.
- **Reprodutível**: `random.Random(42)` e uma semente fixa dão sempre os mesmos
  valores.
- **Idempotente**: se as 1.000.000 de linhas já existirem, não altera nada.

## Tarefa 2 — tempos medidos

Cada base foi recriada do zero a partir do *template* `pagila`
(`--pagila --reset`) antes de cada medição.

```
### ch04_a
ch04_a: inserted 1000000 rentals (100001..1100000)

real    0m19.479s
user    0m6.881s
sys     0m0.232s

### ch04_b
ch04_b: inserted 1000000 rentals (100001..1100000)

real    0m19.289s
user    0m6.959s
sys     0m0.188s
```

**~19,5 s** e **~19,3 s** — bem abaixo do limite de 30 s.

## Tarefa 3 — as duas bases ficam iguais

Checksum pedido no enunciado, corrido nas duas bases:

```sql
SELECT md5(string_agg(concat_ws('|', rental_id, rental_date, inventory_id, customer_id, return_date, staff_id), ',' ORDER BY rental_id))
FROM rental WHERE rental_id > 100000;
```

```
ch04_a:  b4bbe4054089b4fa97d0cfd3628feb14   (1000000 linhas novas)
ch04_b:  b4bbe4054089b4fa97d0cfd3628feb14   (1000000 linhas novas)
```

Checksums iguais: as linhas novas são exatamente as mesmas nas duas bases.

## Tarefa 4 — idempotência

Segunda corrida sobre `ch04_a`:

```
$ uv run python seed.py ch04_a
ch04_a: already seeded (1000000 rows), nothing changed

real    0m0.779s
```

O script deteta que as 1.000.000 de linhas já existem e não escreve nada. Antes
e depois da segunda corrida:

```
              | antes           | depois
--------------+-----------------+----------------
linhas novas  | 1000000         | 1000000
checksum      | b4bbe4054089... | b4bbe4054089...
```

A contagem e o checksum ficam inalterados.

## Verificação de validade

Sobre `ch04_a` (o mesmo vale para `ch04_b`):

```
total_rental        | 1051805   (51805 originais + 1000000 novos)
new_rows            | 1000000
broken_fk           | 0
return_before_rental| 0
date_out_of_range   | 0
dup_unique_triple   | 0
seq_last_value      | 1100000
```

A sequência fica em 1100000 e o próximo `INSERT` sem id recebe 1100001
(confirmado num `INSERT ... RETURNING rental_id` seguido de `ROLLBACK`).

## Porque é que o carregamento é rápido

O Pagila tem três *foreign keys* em `rental` (`inventory_id`, `customer_id`,
`staff_id`). Com as verificações normais, cada uma das 1.000.000 de linhas
obriga a três *lookups* de índice. O script desliga-as durante o `COPY`:

```sql
SET session_replication_role = replica;
```

Comparação medida (mesma máquina, base recriada do zero em cada caso):

```
sem session_replication_role = replica :  43,6 s
com session_replication_role = replica :  19,4 s
```

**Cuidado**: isto só é seguro porque sabemos que os dados são válidos. Os
índices **únicos não são afetados** por `session_replication_role` — o
`UNIQUE (rental_date, inventory_id, customer_id)` continua a ser imposto durante
o `COPY`. E, logo a seguir ao carregamento, o script confirma explicitamente
todas as chaves estrangeiras e aborta se houver alguma quebrada:

```sql
SELECT count(*)
FROM rental r
LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
LEFT JOIN customer  c ON c.customer_id  = r.customer_id
LEFT JOIN staff     s ON s.staff_id     = r.staff_id
WHERE r.rental_id BETWEEN 100001 AND 1100000
  AND (i.inventory_id IS NULL OR c.customer_id IS NULL OR s.staff_id IS NULL);
-- 0
```

Só depois disto é que faz `RESET session_replication_role` e o `COMMIT`. Isto
exige um utilizador com privilégios de superutilizador (o `postgres`).

## Nota: a sequência do Pagila não está "owned" pela coluna

O `setval` não pode usar `pg_get_serial_sequence('rental', 'rental_id')`: neste
Pagila a sequência `rental_rental_id_seq` é ligada à coluna por um simples
`DEFAULT nextval(...)`, sem a relação de *ownership* que o `SERIAL` cria. Por
isso `pg_get_serial_sequence` devolve `NULL` e, como `setval` é uma função
*strict*, a chamada era um no-op silencioso — a sequência ficava em 87559 em vez
de 1100000.

O `seed.py` trata disso com o auxiliar `rental_id_sequence()`: tenta primeiro
`pg_get_serial_sequence` e, se vier `NULL`, extrai o nome da sequência do
`DEFAULT` da coluna (`nextval('rental_rental_id_seq'...)`). Assim o `setval`
funciona e a sequência fica mesmo em 1100000.
