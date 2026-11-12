# Exercise 08 — Transações e concorrência

**Objetivo.** Reproduzir lost updates, deadlocks e write skew, e corrigir cada um.

## Ficheiros

- `setup.sql` — corre uma vez em `ex08`: adiciona `customer.balance` e leva a loja 1 de 6 para 20 staff ativos.
- `reproduce.py` — reproduz as tarefas 1, 2a, 2b e 3 com duas ligações.
- `lost_update.md` — tabelas das duas sessões e resultados das tarefas 1 e 2.
- `deadlock.md` — tabela das duas sessões, mensagem completa de erro e explicação.
- `write_skew.py` — tarefa 4 (20 threads, `Barrier(20)`).

## Como correr

```bash
./scripts/create-db.sh ex08 --pagila --reset
docker compose exec -T postgres psql -U postgres -d ex08 \
    -v ON_ERROR_STOP=1 < exercises/08-transactions/exercise/setup.sql

cd exercises/08-transactions/exercise
uv run python reproduce.py     # tarefas 1, 2a, 2b, 3
uv run python write_skew.py    # tarefa 4
```

## Tarefas 1 a 3

Ver `lost_update.md` e `deadlock.md`. Resumo:

| Tarefa | Resultado |
|--------|-----------|
| 1 — lost update (read-then-write) | saldo final **90** (devia ser 80) |
| 2a — `UPDATE` atómico | saldo final **80** |
| 2b — `SELECT ... FOR UPDATE` | saldo final **80** |
| 3 — deadlock | `ERROR: deadlock detected`, `SQLSTATE 40P01`, uma sessão abortada |

## Tarefa 4 — write skew

A regra é "cada loja mantém pelo menos um membro de staff ativo". `write_skew.py`
arranca 20 threads (uma por membro ativo da loja 1), cada uma com a sua ligação.
Cada thread corre uma transação: conta os ativos da loja 1; se a contagem for
maior que 1, põe-se a si própria a `active = false`; `COMMIT`. Um
`threading.Barrier(20)` entre a contagem e o update garante que todas leem antes
de qualquer uma escrever.

### 4.1 — `READ COMMITTED`

```
======================================================================
Task 4.1 - READ COMMITTED (expect 0 active staff: the rule is broken)
======================================================================
active staff of store 1 afterwards: 0
transactions by number of attempts: {1: 20}
```

As 20 threads leem todas `count = 20`, todas concluem que podem sair, e todas
escrevem `active = false`. A loja fica com **0** membros ativos — a regra é
violada.

### 4.3 — `SERIALIZABLE` com retries

```
======================================================================
Task 4.3 - SERIALIZABLE with retries (expect exactly 1 active)
======================================================================
active staff of store 1 afterwards: 1
transactions by number of attempts: {1: 1, 2: 2, 3: 2, 4: 1, 5: 1, 6: 2, 7: 1, 8: 1, 9: 1, 11: 2, 12: 1, 14: 2, 16: 1, 20: 1, 22: 1}
total serialisation retries: 156
```

Fica exatamente **1** membro ativo. Uma segunda execução dá o mesmo resultado
(0 na 4.1, 1 na 4.3), com um número de retries diferente:

```
active staff of store 1 afterwards: 1
total serialisation retries: 153
```

### Porque é que `READ COMMITTED` quebra a regra

Sob `READ COMMITTED`, cada statement vê apenas os dados já committed antes de
começar. O `SELECT count(*)` e o `UPDATE` são statements separados: o
`Barrier(20)` força todas as threads a ler antes de qualquer escrita, por isso
as 20 veem o mesmo snapshot (`count = 20`). Nenhuma vê a escrita das outras,
todas acham que sobram colegas, e todas saem. É um **write skew**: cada
transação, sozinha, mantém a regra (havia 20 ativos, sair um deixa 19), mas o
conjunto viola-a. Não é um lost update porque nenhuma linha é escrita duas
vezes — são 20 linhas diferentes, cada uma escrita uma vez. Um `CHECK` ou
`UNIQUE` não ajudam aqui: a regra é sobre o *conjunto* de linhas, não sobre uma
linha.

### Porque é que `SERIALIZABLE` não quebra

`SERIALIZABLE` usa *serializable snapshot isolation* (SSI): além de ver um
snapshot, o motor registra as dependências de leitura/escrita entre transações.
Quando duas transações leem as mesmas linhas e escrevem em conflito — o padrão
exato deste exercício — uma delas é abortada com `SQLSTATE 40001`
(`serialization_failure`). O `write_skew.py` interceta esse erro e **repete a
transação do início**, agora sem a barreira: a primeira a repetir vê
`count = 20` e sai (fica 19); a seguinte vê 19 e sai; e assim por diante, até uma
ver `count = 1` e não sair. No fim fica **exatamente 1** ativo, como se as
transações tivessem corrido uma após a outra.

## Done when

- [x] lost update reproduzido (90) e explicado
- [x] deadlock reproduzido e explicado linha a linha
- [x] as duas correções dão saldo final 80
- [x] `READ COMMITTED` deixa menos de 1 ativo (0)
- [x] `SERIALIZABLE` deixa exatamente 1 ativo
