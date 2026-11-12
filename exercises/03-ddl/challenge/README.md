# Challenge 03 — A base de dados recusa ISBNs inválidos

**Objetivo.** Fazer com que seja a própria base de dados a rejeitar ISBN-13
inválidos, através de um `DOMAIN` com um `CHECK`.

## Ficheiro

- `isbn.sql` — a função `is_valid_isbn13(text)`, o domínio `isbn13`, a tabela
  `book` e os 7 `INSERT` de teste.

## Como correr

Na raiz do repositório:

```bash
./scripts/create-db.sh ch03
docker compose exec -T postgres psql -U postgres -d ch03 < exercises/03-ddl/challenge/isbn.sql
```

O ficheiro corre **sem** `ON_ERROR_STOP`: os 4 últimos `INSERT` têm de falhar,
por isso o psql continua depois de cada erro.

## Saída

```
DROP TABLE
DROP DOMAIN
DROP FUNCTION
CREATE FUNCTION
CREATE DOMAIN
CREATE TABLE
INSERT 0 1
INSERT 0 1
INSERT 0 1
 book_id |       isbn        |       title
---------+-------------------+-------------------
       1 | 978-0-306-40615-7 | Com hifens
       2 | 9781402894626     | Sem hifens
       3 | 978-3-16-148410-0 | Outro ISBN valido
(3 rows)

ERROR:  value for domain isbn13 violates check constraint "isbn13_check"
ERROR:  value for domain isbn13 violates check constraint "isbn13_check"
ERROR:  value for domain isbn13 violates check constraint "isbn13_check"
ERROR:  value for domain isbn13 violates check constraint "isbn13_check"
```

Os 3 valores válidos são aceites e ficam na tabela. Os 4 valores inválidos são
rejeitados pelo domínio:

| Valor | Motivo da rejeição |
|---|---|
| `978-0-306-40615-8` | dígito de controlo errado (devia ser `7`) |
| `978-0-306-4061` | demasiado curto (12 dígitos) |
| `-9780306406157` | hífen no início |
| `978--0306406157` | dois hífens seguidos |

## Como a função valida

1. **Formato** — a expressão regular `^[0-9]+(-[0-9]+)*$` só aceita dígitos,
   com hífens entre grupos de dígitos. Isto exclui hífen no início, no fim ou
   dois seguidos.
2. **Comprimento** — depois de remover os hífens, têm de sobrar exatamente
   13 dígitos.
3. **Dígito de controlo** — os 12 primeiros dígitos são multiplicados
   alternadamente por `1` e `3`, somam-se e o dígito de controlo é
   `(10 - soma % 10) % 10`. Tem de ser igual ao 13.º dígito.

## 4. Porque é que a função tem de ser `IMMUTABLE`

`IMMUTABLE` promete duas coisas: para as **mesmas entradas** a função devolve
**sempre o mesmo resultado**, e não lê nem altera nada do estado da base de
dados (tabelas, hora atual, `search_path`, definições da sessão).

É obrigatório aqui por dois motivos:

- **É usada num `CHECK`** (do domínio `isbn13`). O PostgreSQL só aceita
  expressões imutáveis num `CHECK`, porque a regra tem de valer para todas as
  linhas, atuais e futuras. Se a função pudesse mudar de resultado (por
  exemplo, se dependesse da data), uma linha válida quando foi inserida podia
  passar a ser inválida sem ser reescrita — o `CHECK` deixaria de ser uma
  garantia. Uma função `VOLATILE` (o valor por omissão) faz o `CREATE DOMAIN`
  falhar com "functions in check constraint expression must be marked
  IMMUTABLE".
- **Permite otimizações.** Ao saber que o resultado é constante, o planner
  pode avaliar a função uma só vez e reutilizar o valor, e poderia usá-la
  numa expressão indexada.

A função é genuinamente imutável: só usa operações puras sobre texto e
números (`replace`, `length`, `substr`, `!~`, `generate_series`, `sum`,
aritmética), sem depender de nada externo.
