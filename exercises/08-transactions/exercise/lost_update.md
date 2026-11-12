# Lost update — reprodução e correção

Base de dados `ex08` (cópia de Pagila) com a coluna `customer.balance` do setup.
Todas as medições usam `reproduce.py` (`uv run python reproduce.py`), que abre
duas ligações separadas e faz o interleaving exatamente como nas tabelas abaixo.
O saldo do cliente 1 é reposto a 100 antes de cada tarefa.

## Tarefa 1 — o lost update

Cada sessão lê o saldo e escreve o valor lido menos 10:

| Sessão A | Sessão B |
|----------|----------|
| `BEGIN;` | |
| `SELECT balance FROM customer WHERE customer_id = 1;` → **100.00** | |
| | `BEGIN;` |
| | `SELECT balance FROM customer WHERE customer_id = 1;` → **100.00** |
| `UPDATE customer SET balance = 90 WHERE customer_id = 1;` | |
| `COMMIT;` | |
| | `UPDATE customer SET balance = 90 WHERE customer_id = 1;` |
| | `COMMIT;` |

Resultado:

```
final balance: 90.00 (lost update: one -10 disappeared)
```

As duas sessões leram 100 antes de qualquer escrita, por isso as duas calcularam
90 e as duas escreveram 90. A segunda escrita passou por cima da primeira e o
primeiro débito de 10 **desapareceu**: o saldo devia ser 80 (100 − 10 − 10) e
ficou 90. Isto é um *lost update*: sob `READ COMMITTED` o `UPDATE` não bloqueia
o `SELECT` que já aconteceu, e a última escrita ganha.

## Tarefa 2a — correção com um `UPDATE` atómico

Leitura e escrita no mesmo statement; a linha fica bloqueada até ao fim da
transação:

| Sessão A | Sessão B |
|----------|----------|
| `BEGIN;` | |
| `UPDATE customer SET balance = balance - 10 WHERE customer_id = 1 AND balance >= 10;` (fica com o lock da linha) | |
| | `BEGIN;` |
| | `UPDATE ... balance = balance - 10 ... AND balance >= 10;` → **espera pelo lock de A** |
| `COMMIT;` | |
| | o `UPDATE` avança, lê o valor já atualizado e escreve |
| | `COMMIT;` |

Resultado:

```
B          still waiting: True
final balance: 80.00
```

Como o `UPDATE` lê e escreve num só passo, B não pode usar um valor velho: fica
bloqueado no lock de linha que A detém e, quando A faz `COMMIT`, o `UPDATE` de B
relê o valor já atualizado (90) e escreve 80. Saldo final **80**, correto.

## Tarefa 2b — correção com `SELECT ... FOR UPDATE`

| Sessão A | Sessão B |
|----------|----------|
| `BEGIN;` | |
| `SELECT balance FROM customer WHERE customer_id = 1 FOR UPDATE;` → **100.00** | |
| | `BEGIN;` |
| | `SELECT balance FROM customer WHERE customer_id = 1 FOR UPDATE;` → **espera por A** |
| `UPDATE customer SET balance = 90 WHERE customer_id = 1;` | |
| `COMMIT;` | |
| | o `SELECT ... FOR UPDATE` de B devolve → **90.00** |
| | `UPDATE customer SET balance = 80 WHERE customer_id = 1;` |
| | `COMMIT;` |

Resultado:

```
B          SELECT ... FOR UPDATE -> 90.00 (read after A committed)
final balance: 80.00
```

O `FOR UPDATE` bloqueia a linha logo na leitura. B espera, e quando A faz
`COMMIT` a leitura de B devolve já o valor novo (90), por isso B escreve 80.
Saldo final **80**, correto.

## Conclusão

| Cenário | Saldo final | Correto? |
|---------|------------:|:--------:|
| Tarefa 1 — read-then-write sem proteção | 90 | não (devia ser 80) |
| Tarefa 2a — `UPDATE` atómico | 80 | sim |
| Tarefa 2b — `SELECT ... FOR UPDATE` | 80 | sim |

A causa é sempre a mesma: separar a leitura da escrita deixa uma janela entre
elas. Ou se faz tudo no mesmo statement (`balance = balance - 10`), ou se
bloqueia a linha entre a leitura e a escrita (`FOR UPDATE`).
