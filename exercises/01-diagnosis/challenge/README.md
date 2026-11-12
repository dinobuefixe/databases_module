# Challenge 01 — Escritas concorrentes: ficheiro JSON vs PostgreSQL

**Objetivo.** Mostrar com números porque é que um motor de base de dados trata
escritas concorrentes e um ficheiro JSON não.

## Ficheiros

- `json_race.py` — 10 processos que fazem *read-modify-write* a `records.json`.
- `pg_race.py` — os mesmos 10 processos a inserir na tabela `record`.
- `pyproject.toml` / `uv.lock` — projeto `uv`.

## Preparação

Na raiz do repositório:

```bash
./scripts/create-db.sh ch01
```

O `pg_race.py` cria a tabela `record` se ela não existir:

```sql
CREATE TABLE record (worker integer NOT NULL, n integer NOT NULL);
```

A ligação vem da variável de ambiente `DATABASE_URL`; se não estiver definida,
o valor por omissão é `postgresql://postgres:change-me-postgres@localhost:5432/ch01`.

## Comandos

```bash
cd exercises/01-diagnosis/challenge
uv run python json_race.py
uv run python pg_race.py
```

Cada script limpa o seu estado no início (`json_race.py` recria `records.json`
com `[]` e `pg_race.py` faz `TRUNCATE record`), por isso cada execução é
independente e pode ser repetida.

## Resultados (3 execuções de cada)

`json_race.py` — 10 processos × 1.000 registos = 10.000 esperados:

| Execução | Registos no ficheiro | Escritas falhadas |
|---------:|---------------------:|------------------:|
| 1 | 28 | 9.961 |
| 2 | 53 | 9.911 |
| 3 | 23 | 9.976 |

`pg_race.py` — 10 processos × 1.000 registos = 10.000 esperados:

| Execução | Linhas em `record` |
|---------:|-------------------:|
| 1 | 10.000 |
| 2 | 10.000 |
| 3 | 10.000 |

## Porque é que os números diferem

No `json_race.py` cada processo faz três passos separados: lê o ficheiro
inteiro, acrescenta um registo em memória e reescreve o ficheiro inteiro. Nada
impede que dois processos leiam o mesmo conteúdo ao mesmo tempo. Ambos
acrescentam o seu registo sobre a mesma versão, o primeiro escreve e o segundo
volta a escrever por cima — **o registo do primeiro desaparece (lost update)**.
Além disso, `open(..., "w")` corta o ficheiro para zero bytes antes de o voltar
a preencher, por isso outro processo pode ler um ficheiro vazio ou a meio de
uma escrita e receber JSON inválido: esse caso é contado como *escrita falhada*
(cerca de 9.900 das 10.000). O total de registos nunca chega perto dos 10.000 e
varia de execução para execução porque depende do escalonamento dos processos.

No `pg_race.py` cada processo tem a sua própria ligação e o motor serializa as
escritas: cada `INSERT` é atómico e bloqueia as linhas/estruturas necessárias
para que duas escritas não se pisem. Nenhum `INSERT` é perdido, logo o
`SELECT count(*)` devolve exatamente **10.000 em todas as execuções**. É a
garantia de concorrência e atomicidade (o C e o I de ACID) que um ficheiro
partilhado não tem.
