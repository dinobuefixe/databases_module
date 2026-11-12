# Exercise 09 — Segurança

**Objetivo.** Aplicar o princípio do menor privilégio nos três motores e escrever
em cada um a partir de uma API, sem injeção.

## Ficheiros

- `roles.sql` — cria os papéis `ex09_migrations`, `ex09_app` e `ex09_readonly` e
  concede os privilégios mínimos. Passa as passwords como variáveis psql, por
  isso não há segredos no ficheiro.
- `proofs.sql` — provas de privilégio com `SET ROLE` / `RESET ROLE`.
- `app/main.py` — API FastAPI com 3 endpoints (PostgreSQL, MongoDB, Redis).
- `.env.example` — nomes das variáveis de ambiente que a API usa.

## Como correr

```bash
./scripts/create-db.sh ex09 --pagila --reset

# 1. Papéis (as passwords vêm do ambiente, nunca do ficheiro)
docker compose exec -T postgres psql -U postgres -d ex09 -v ON_ERROR_STOP=1 \
    -v migrations_password="$EX09_MIGRATIONS_PASSWORD" \
    -v app_password="$EX09_APP_PASSWORD" \
    -v readonly_password="$EX09_READONLY_PASSWORD" \
    -f - < exercises/09-security/exercise/roles.sql

# 2. Provas (espera erros, por isso sem ON_ERROR_STOP)
docker compose exec -T postgres psql -U postgres -d ex09 \
    -f - < exercises/09-security/exercise/proofs.sql

# 3. Utilizadores de MongoDB e Redis
docker compose exec -T mongo mongosh \
    "mongodb://root:$MONGO_ROOT_PASSWORD@localhost:27017/?authSource=admin" --quiet --eval '
db = db.getSiblingDB("ex09");
db.createUser({ user: "ex09_app", pwd: process.env.EX09_APP_PASSWORD,
  roles: [{ role: "readWrite", db: "ex09" }] });'

docker compose exec -T redis redis-cli -a "$REDIS_PASSWORD" \
    ACL SETUSER ex09_app on ">$EX09_APP_PASSWORD" '~*' +@all -@dangerous

# 4. API
cd exercises/09-security/exercise
export EX09_PG_DSN="postgresql://ex09_app:$EX09_APP_PASSWORD@localhost:5432/ex09"
export EX09_MONGO_URL="mongodb://ex09_app:$EX09_APP_PASSWORD@localhost:27017/ex09?authSource=ex09"
export EX09_REDIS_URL="redis://ex09_app:$EX09_APP_PASSWORD@localhost:6379/0"
uv run uvicorn app.main:app --port 8000
```

## Tarefa 2 — output de `proofs.sql`

```
SET
psql:<stdin>:11: ERROR:  must be owner of table film
RESET
SET
INSERT 0 1
RESET
SET
 films
-------
  1000
(1 row)

RESET
SET
psql:<stdin>:26: ERROR:  permission denied for table actor
RESET
```

| Prova | Papel | Esperado | Obtido |
|-------|-------|----------|--------|
| `DROP TABLE film` | `ex09_app` | `must be owner of table film` (42501) | igual |
| `INSERT INTO actor ...` | `ex09_app` | `INSERT 0 1` | igual |
| `SELECT count(*) FROM film` | `ex09_readonly` | 1000 | 1000 |
| `INSERT INTO actor ...` | `ex09_readonly` | `permission denied for table actor` (42501) | igual |

## Tarefa 4 — a API é segura

Pedidos e respostas (a API a correr em `127.0.0.1:8000`):

```
$ curl -s -X POST localhost:8000/actors -H 'Content-Type: application/json' \
      -d '{"first_name":"ALICE","last_name":"TESTER"}'
{"actor_id":202}                                    HTTP 201

$ curl -s -X POST localhost:8000/actors -H 'Content-Type: application/json' \
      -d '{"first_name":"x'"'"'); DROP TABLE actor; --","last_name":"y"}'
{"actor_id":203}                                    HTTP 201

$ curl -s -X POST localhost:8000/notes -H 'Content-Type: application/json' \
      -d '{"customer_id":1,"text":"hello"}'
{"inserted_id":"6af621f8e4d416559fc72e6b"}          HTTP 201

$ curl -s -X POST localhost:8000/notes -H 'Content-Type: application/json' \
      -d '{"customer_id":1,"text":{"$ne":null}}'
{"detail":[{"type":"string_type","loc":["body","text"],
  "msg":"Input should be a valid string","input":{"$ne":null}}]}   HTTP 422

$ curl -s -X POST localhost:8000/counters/foo
{"name":"foo","value":1}                            HTTP 200

$ curl -s -X POST 'localhost:8000/counters/a*'
{"detail":"name must match ^[a-z0-9_-]{1,32}$"}     HTTP 422

$ curl -s -X POST 'localhost:8000/counters/x:y'
{"detail":"name must match ^[a-z0-9_-]{1,32}$"}     HTTP 422
```

O que ficou guardado:

```
actor_id | first_name                  | last_name
---------+-----------------------------+-----------
     202 | ALICE                       | TESTER
     203 | x'); DROP TABLE actor; --   | y
```

A tentativa de injeção foi guardada **literalmente** na coluna `first_name` e a
tabela `actor` continua a existir (`SELECT to_regclass('public.actor')` → `actor`).
Isto porque a query é parametrizada:

```python
conn.execute(
    "INSERT INTO actor (first_name, last_name) VALUES (%s, %s) RETURNING actor_id",
    (body.first_name, body.last_name),
)
```

O texto e o SQL viajam separados; o motor nunca trata o valor como código. O
mesmo princípio em cada motor:

- **PostgreSQL** — `%s` no psycopg (nunca `f"...'{valor}'"`).
- **MongoDB** — o corpo é validado pelo Pydantic antes de chegar ao `insert_one`;
  `text` tem de ser `str`, por isso o operador `{"$ne": null}` devolve 422.
- **Redis** — o `name` é validado contra `^[a-z0-9_-]{1,32}$` antes do `INCR`;
  `a*` e `x:y` devolvem 422.

## Nota sobre o Redis ACL

`ACL SETUSER` só vive em memória. Quando o Redis reinicia, o utilizador
`ex09_app` **desaparece** e a API deixa de se conseguir autenticar. Para o
manter, é preciso escrevê-lo num ficheiro de ACL e dizê-lo ao servidor:

```bash
docker compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ACL SAVE
```

e no `redis.conf` (ou no comando de arranque):

```
aclfile /data/users.acl
```

Com `aclfile` definido, o `ACL SAVE` grava os utilizadores no ficheiro e o
Redis volta a carregá-los no arranque seguinte. Sem isto, a criação dos
utilizadores tem de ser repetida sempre que o contentor é recriado.
