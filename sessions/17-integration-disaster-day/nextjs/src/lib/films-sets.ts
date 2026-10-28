// customer:{id}:films: the films each customer has rented. Derived from PostgreSQL (session 16).
import type { RedisClientType } from "redis";
import { prisma } from "@/lib/prisma";

export const filmsKey = (customerId: number) => `customer:${customerId}:films`;

// Rebuilds every set with one query and one pipeline; a temporary key and RENAME per customer.
export async function rebuildAll(redis: RedisClientType) {
  const rows = await prisma.$queryRaw<{ customer_id: number; film_ids: number[] }[]>`
    SELECT c.customer_id,
           coalesce(array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL), '{}') AS film_ids
    FROM customer c
    LEFT JOIN rental r    ON r.customer_id = c.customer_id
    LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
    GROUP BY c.customer_id`;
  const pipeline = redis.multi();
  for (const { customer_id, film_ids } of rows) {
    const key = filmsKey(customer_id);
    pipeline.del(`${key}:rebuild`);
    if (film_ids.length > 0) {
      pipeline.sAdd(`${key}:rebuild`, film_ids.map(String));
      pipeline.rename(`${key}:rebuild`, key);
    } else {
      pipeline.del(key);
    }
  }
  await pipeline.execAsPipeline();
  return rows.length;
}

// Compares the size of every set with PostgreSQL.
export async function verify(redis: RedisClientType) {
  const rows = await prisma.$queryRaw<{ customer_id: number; expected: bigint }[]>`
    SELECT r.customer_id, count(DISTINCT i.film_id) AS expected
    FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
    GROUP BY r.customer_id`;
  const pipeline = redis.multi();
  for (const row of rows) pipeline.sCard(filmsKey(row.customer_id));
  const actual = (await pipeline.execAsPipeline()) as unknown as number[];
  const mismatches = rows
    .map((row, i) => ({ customer_id: row.customer_id, redis: actual[i], postgres: Number(row.expected) }))
    .filter((m) => m.redis !== m.postgres);
  return { checked: rows.length, mismatches };
}
