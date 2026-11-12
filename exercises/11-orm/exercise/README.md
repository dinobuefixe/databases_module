# Exercise 11 — ORM I, SQLAlchemy

**Objetivo.** Mapear tabelas existentes para modelos ORM, comparar o SQL gerado
com SQL escrito à mão, e encontrar e corrigir um N+1.

## Ficheiros

- `models.py` — modelos 2.0 (`Mapped` / `mapped_column`) para `film`,
  `language`, `actor`, `film_actor`, `category`, `film_category`.
- `queries.py` — as 3 queries em ORM e a versão handwritten, com `echo=True`.
- `n_plus_one.py` — o N+1 e a correção com `selectinload`.

## Como correr

```bash
./scripts/create-db.sh ex11 --pagila --reset
cd exercises/11-orm/exercise
uv run python queries.py      # task 2 (imprime o SQL gerado)
uv run python n_plus_one.py   # task 3
```

## Tarefa 1 — modelos

`Film` tem `language` (N:1), `actors` e `categories` (N:N através das tabelas de
associação `film_actor` e `film_category`). `Actor` e `Category` têm `films`.
`Language` tem `films`. As duas tabelas de associação são `Table(...)` no
`Base.metadata`, com chave primária composta.

## Tarefa 2 — ORM vs SQL escrito à mão

As três queries ORM devolvem **exatamente as mesmas linhas** que o SQL à mão
(verificado no próprio script com `assert`):

```
Q1 films per category: 16 rows, same as handwritten SQL: True
Q2 films longer than average: 489 rows, same as handwritten SQL: True
Q3 top 10 actors: 10 rows, same as handwritten SQL: True
```

### Q1 — filmes por categoria

Handwritten:

```sql
SELECT c.name, count(*) AS films
FROM category c JOIN film_category fc ON fc.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY films DESC, c.name;
```

Gerado pelo ORM:

```sql
SELECT category.name, count(film.film_id) AS films
FROM category
JOIN film_category AS film_category_1
     ON category.category_id = film_category_1.category_id
JOIN film ON film.film_id = film_category_1.film_id
GROUP BY category.category_id, category.name
ORDER BY count(film.film_id) DESC, category.name;
```

Diferenças: o ORM acrescenta o `JOIN film` (porque navega a relação `films`, que
passa pela associação e chega a `film`) e conta `film.film_id` em vez de `*`.
Como cada linha de `film_category` corresponde a um filme, o resultado é o
mesmo. O `ORDER BY` é repetido com a expressão `count(...)` em vez do alias.

### Q2 — filmes mais longos que a média

Handwritten:

```sql
SELECT f.film_id, f.title, f.length
FROM film f
WHERE f.length > (SELECT avg(length) FROM film)
ORDER BY f.length DESC, f.film_id;
```

Gerado pelo ORM:

```sql
SELECT film.film_id, film.title, film.length
FROM film
WHERE film.length > (
    SELECT avg(film.length) AS avg_1 FROM film
)
ORDER BY film.length DESC, film.film_id;
```

A forma é praticamente idêntica: a subquery é escalar (`scalar_subquery()`), com
um alias interno `avg_1`. O ORM qualifica todas as colunas com o nome da tabela.

### Q3 — os 10 atores com mais filmes

Handwritten:

```sql
SELECT a.actor_id, a.first_name, a.last_name, count(*) AS films
FROM actor a JOIN film_actor fa ON fa.actor_id = a.actor_id
GROUP BY a.actor_id
ORDER BY films DESC, a.actor_id
LIMIT 10;
```

Gerado pelo ORM:

```sql
SELECT actor.actor_id, actor.first_name, actor.last_name,
       count(film.film_id) AS films
FROM actor
JOIN film_actor AS film_actor_1 ON actor.actor_id = film_actor_1.actor_id
JOIN film ON film.film_id = film_actor_1.film_id
GROUP BY actor.actor_id
ORDER BY count(film.film_id) DESC, actor.actor_id
LIMIT %(param_1)s::INTEGER;
```

Diferenças: o ORM acrescenta o `JOIN film` e conta `film.film_id`; o `LIMIT` é um
parâmetro ligado (`%(param_1)s`) em vez do literal `10`. O `GROUP BY a.actor_id`
funciona porque `actor_id` é a chave primária e as restantes colunas dependem
funcionalmente dela.

## Tarefa 3 — N+1

`n_plus_one.py` carrega os primeiros 100 filmes por `film_id` e imprime o título
com os nomes dos atores, acedendo a `film.actors`.

| Versão | SELECTs |
|--------|--------:|
| N+1 (relação lazy) | **101** |
| Corrigida (`selectinload(Film.actors)`) | **2** |

O contador é um listener `before_cursor_execute` no engine que conta os
statements que começam por `SELECT`.

Na versão N+1 há 1 query para os 100 filmes e depois **uma por cada filme** para
carregar os atores: 1 + 100 = 101. Na versão corrigida, `selectinload` faz uma
query para os filmes e uma segunda query `WHERE film_id IN (...)` para todos os
atores, num total de 2. É por isso que o N+1 é invisível com 20 linhas e
doloroso com 2.000.

## Done when

- [x] as 3 queries ORM devolvem as mesmas linhas que o SQL à mão
- [x] a versão N+1 corre 101 queries
- [x] a versão corrigida corre no máximo 2
