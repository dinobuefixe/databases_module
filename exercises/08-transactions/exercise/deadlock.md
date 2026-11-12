# Deadlock — reprodução e explicação

Base de dados `ex08`. Reproduzido por `reproduce.py` (tarefa 3), com duas
ligações separadas. A sessão A bloqueia o cliente 1 e depois o cliente 2; a
sessão B bloqueia o cliente 2 e depois o cliente 1.

## Interleaving

| Sessão A | Sessão B |
|----------|----------|
| `BEGIN;` | |
| `UPDATE customer SET balance = balance - 1 WHERE customer_id = 1;` (lock no cliente 1) | |
| | `BEGIN;` |
| | `UPDATE customer SET balance = balance - 1 WHERE customer_id = 2;` (lock no cliente 2) |
| `UPDATE customer SET balance = balance - 1 WHERE customer_id = 2;` → **espera pelo lock de B** | |
| | `UPDATE customer SET balance = balance - 1 WHERE customer_id = 1;` → **espera pelo lock de A** |

Neste ponto há um ciclo: A tem o cliente 1 e quer o 2; B tem o 2 e quer o 1.
Nenhum dos dois pode avançar. Ao fim de `deadlock_timeout` (1 segundo por
omissão) o PostgreSQL deteta o ciclo e aborta uma das transações.

## Mensagem completa devolvida pelo servidor

```
--- session B aborted ---
SQLSTATE: 40P01
ERROR:  deadlock detected
DETAIL: Process 6651 waits for ShareLock on transaction 1447; blocked by process 6650.
DETAIL: Process 6650 waits for ShareLock on transaction 1448; blocked by process 6651.
HINT:   See server log for query details.
CONTEXT: while locking tuple (17,2) in relation "customer"
```

(Os números de processo e de transação mudam de execução para execução; o que
não muda é a forma da mensagem.)

## Explicação linha a linha

- **`ERROR:  deadlock detected`** — o detetor de deadlocks encontrou um ciclo de
  espera entre transações e abortou uma delas para quebrá-lo.
- **`SQLSTATE: 40P01`** — o código do erro (`deadlock_detected`). É este o código
  que a aplicação deve intercetar para repetir a transação.
- **`DETAIL: Process 6651 waits for ShareLock on transaction 1447; blocked by
  process 6650.`** — o processo 6651 (a sessão B) está à espera de um
  `ShareLock` detido pela transação 1447, que pertence ao processo 6650 (a
  sessão A). Em `UPDATE`, o `ShareLock` é o lock de linha: B quer a linha que A
  já bloqueou.
- **`DETAIL: Process 6650 waits for ShareLock on transaction 1448; blocked by
  process 6651.`** — a segunda metade do ciclo: A espera por uma linha que B
  bloqueou. As duas linhas `DETAIL` juntas mostram o ciclo A→B→A.
- **`HINT:   See server log for query details.`** — a mensagem enviada ao
  cliente é resumida; o log do servidor tem o texto exato dos statements.
- **`CONTEXT: while locking tuple (17,2) in relation "customer"`** — o statement
  que ficou bloqueado estava a tentar bloquear o tuplo (17,2) da tabela
  `customer` (o par físico `(página, linha)`), ou seja, a segunda linha que
  aquela sessão queria.

## Como prevenir

1. **Bloquear sempre pela mesma ordem.** Se A e B atualizassem sempre o cliente
   de menor id primeiro, B ficaria simplesmente à espera de A e nunca haveria
   ciclo. É a defesa principal: impor uma ordem global (por exemplo, `ORDER BY
   customer_id`) a tudo o que bloqueie mais do que uma linha.
2. **Manter as transações curtas** e não fazer trabalho lento (chamadas HTTP,
   esperas) enquanto se detêm locks: menos tempo com locks, menos janelas para
   um ciclo.
3. **Repetir a transação abortada.** Mesmo com boa ordem, um deadlock é sempre
   possível; a aplicação deve intercetar `SQLSTATE 40P01` e voltar a tentar a
   transação do início.
