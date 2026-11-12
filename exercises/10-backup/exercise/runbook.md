# Runbook — recuperar a base `ex10` de um `DELETE` sem `WHERE`

## Quando usar

Alguém correu `disaster.sql` em `ex10` e apagou dados de produção por engano
(um `DELETE` sem filtro correto). A base ainda existe e está a aceitar ligações;
não se quer recriá-la (perde-se o que aconteceu depois do backup que não seja
recuperável do dump). Este runbook restaura **apenas** as linhas apagadas.

## Pré-requisitos

- Acesso ao servidor onde corre o PostgreSQL (aqui via `docker compose`).
- O dump mais recente em `backups/` (formato custom, `-Fc`).
- Espaço em disco para o dump e para a operação.
- Conhecer as partições afetadas: `payment` é particionada por mês.

## Passo 0 — avaliar a situação (sem escrever nada)

```bash
# contar as linhas das três tabelas afetadas
docker compose exec -T postgres psql -U postgres -d ex10 -c "
SELECT 'payment' AS t, count(*) FROM payment
UNION ALL SELECT 'film_actor', count(*) FROM film_actor
UNION ALL SELECT 'film_category', count(*) FROM film_category;"

# confirmar as partições de payment
docker compose exec -T postgres psql -U postgres -d ex10 -c "
SELECT c.relname FROM pg_inherits i
JOIN pg_class c ON c.oid = i.inhrelid
WHERE i.inhparent = 'payment'::regclass ORDER BY 1;"
```

Neste incidente, os valores eram: `payment` 45780, `film_actor` 4135,
`film_category` 2218.

## Passo 1 — identificar o dump a usar

```bash
ls -t backups/ex10_*.dump | head -1
# backups/ex10_2026-11-12_2031.dump
DUMP=$(ls -t backups/ex10_*.dump | head -1)
```

## Passo 2 — restaurar as partições de `payment` afetadas

O `disaster.sql` apagou `payment WHERE payment_date >= '2026-01-01'`, ou seja
as partições `payment_p2026_01` a `payment_p2026_07`. Como as restantes
partições não foram tocadas, esvaziam-se só estas e recarrega-se o dump:

```bash
docker compose exec -T postgres psql -U postgres -d ex10 -v ON_ERROR_STOP=1 -c "
TRUNCATE payment_p2026_01, payment_p2026_02, payment_p2026_03, payment_p2026_04,
         payment_p2026_05, payment_p2026_06, payment_p2026_07,
         film_actor, film_category;"
```

## Passo 3 — recarregar os dados do dump

```bash
time docker compose exec -T postgres pg_restore -U postgres -d ex10 --data-only \
  -t payment_p2026_01 -t payment_p2026_02 -t payment_p2026_03 -t payment_p2026_04 \
  -t payment_p2026_05 -t payment_p2026_06 -t payment_p2026_07 \
  -t film_actor -t film_category < "$DUMP"
```

`payment` está particionada: `-t payment` não restaura nada, é preciso nomear
cada partição. `film_actor` e `film_category` são tabelas normais, por isso
`-t` funciona diretamente.

## Passo 4 — verificar o restauro

```bash
docker compose exec -T postgres psql -U postgres -d ex10 -c "
SELECT 'payment' AS t, count(*) FROM payment
UNION ALL SELECT 'film_actor', count(*) FROM film_actor
UNION ALL SELECT 'film_category', count(*) FROM film_category;"
```

As contagens têm de voltar a ser as do momento do backup: **`payment` 51061,
`film_actor` 5462, `film_category` 2367**. Uma verificação adicional útil é um
agregado conhecido que não dependa das linhas novas:

```bash
docker compose exec -T postgres psql -U postgres -d ex10 -c "SELECT sum(amount) FROM payment;"
# 170962.39
```

Se as contagens não baterem certo, **parar** e não voltar a escrever na base.

## Contagens, antes e depois

| Momento | payment | film_actor | film_category |
|---------|--------:|-----------:|--------------:|
| Tarefa 1 — momento do backup | 51061 | 5462 | 2367 |
| Tarefa 3 — depois de `activity.sql` | 51066 | 5462 | 2367 |
| Tarefa 3 — depois de `disaster.sql` | 45780 | 4135 | 2218 |
| Tarefa 5 — depois do restauro | **51061** | **5462** | **2367** |

O `disaster.sql` apagou 5286 linhas de `payment`, 1327 de `film_actor` e 149 de
`film_category`.

## Tempo real de recuperação (RTO)

```
real    0m0.944s     # só o pg_restore dos dados (passo 3)
```

O procedimento completo (passos 2 e 3) fica em **~2 segundos**, para uma base de
4,4 MB. É rápido porque o dump é pequeno e só se recarregam 9 tabelas. Com uma
base maior, o RTO cresce com o tamanho das partições a recarregar — vale a pena
medir num ensaio.

## Dados perdidos (RPO)

Entre o backup (passo 1 do exercício) e o incidente correu `activity.sql`, que
inseriu 5 pagamentos com `payment_date = '2026-07-30 12:00+00'`. Esses 5
pagamentos **não estão no backup**, por isso o restauro não os recupera:

```sql
SELECT count(*) FROM payment WHERE payment_date = timestamptz '2026-07-30 12:00+00';
-- 0

SELECT max(payment_date) FROM payment;
-- 2026-07-28 23:59:59+00
```

Os 5 alugueres que deviam ter gerado esses pagamentos (os 5 mais recentes)
foram:

```
rental_id | customer_id | staff_id
----------+-------------+----------
    87559 |           3 |        1
    87558 |         676 |        2
    87557 |         484 |        1
    87556 |         715 |        2
    87555 |         250 |        2
```

O **RPO real** é o intervalo entre o backup e o incidente. Neste caso o backup
foi às 20:31 e o `activity.sql` correu logo a seguir, por isso perdeu-se o
trabalho feito nesse intervalo (os 5 pagamentos). O RPO é, portanto, "desde o
último backup até ao incidente".

## O que mudaria na estratégia de backup

- **Backups mais frequentes** (por exemplo a cada hora, ou WAL archiving com
  point-in-time recovery) para reduzir o RPO de "desde o último backup" para
  minutos ou segundos. Com PITR restaurar-se-ia até ao instante *antes* do
  `DELETE`, e os 5 pagamentos também voltariam.
- **Testar o restauro regularmente** num contentor limpo: um backup que nunca
  foi restaurado não é um backup.
- **Retenção** (7 diários, 4 semanais) e um sítio fora do volume Docker: um
  `docker compose down -v` apaga o volume, por isso o dump tem de viver fora
  dele.
- **`pg_dump` não guarda os papéis**: guardar também `pg_dumpall --roles-only`.
- **Reduzir o raio de ação do erro**: o `disaster.sql` apagou em três tabelas
  porque o `DELETE` não tinha `WHERE` correto; um utilizador de aplicação sem
  `DELETE` em `payment` (ver sessão 09) teria evitado parte do estrago.
