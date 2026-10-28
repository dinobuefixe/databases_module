// customer:{id}:films: the films each customer has rented, derived from PostgreSQL (session 16).
import type { RedisClientType } from "redis";
import { prisma } from "@/lib/prisma";

export const filmsKey = (customerId: number) => `customer:${customerId}:films`;

// One query for every customer, one pipeline for every Redis command; temporary key and RENAME.
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
  const mismatches = rows.filter((row, i) => actual[i] !== Number(row.expected)).length;
  return { checked: rows.length, mismatches };
}
