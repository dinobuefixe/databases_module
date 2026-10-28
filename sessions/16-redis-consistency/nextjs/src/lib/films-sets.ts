// customer:{id}:films holds the ids of the films a customer has rented.
// It is derived data: PostgreSQL is the source of truth and the set can always be rebuilt from it.
import type { RedisClientType } from "redis";
import { prisma, prismaReadonly } from "@/lib/prisma";

export const filmsKey = (customerId: number) => `customer:${customerId}:films`;

// Writes the new members to a temporary key and RENAMEs it over the real one, so a reader
// sees the old set or the new one, never a half-built one.
function queueReplace(multi: ReturnType<RedisClientType["multi"]>, customerId: number, filmIds: number[]) {
  const key = filmsKey(customerId);
  const tmp = `${key}:rebuild`;
  multi.del(tmp);
  if (filmIds.length > 0) {
    multi.sAdd(tmp, filmIds.map(String));
    multi.rename(tmp, key);
  } else {
    multi.del(key);
  }
}

// The tutorial's first version: one query per customer, one MULTI/EXEC per customer.
export async function rebuildPerCustomer(redis: RedisClientType) {
  const customers = await prismaReadonly.customer.findMany({ select: { customer_id: true } });
  for (const { customer_id } of customers) {
    const rows = await prismaReadonly.$queryRaw<{ film_id: number }[]>`
      SELECT DISTINCT i.film_id
      FROM rental r JOIN inventory i ON i.inventory_id = r.inventory_id
      WHERE r.customer_id = ${customer_id}`;
    const multi = redis.multi();
    queueReplace(multi, customer_id, rows.map((r) => r.film_id));
    await multi.exec();
  }
  return customers.length;
}

// The rewrite: every customer's films in one query, every Redis command in one pipeline.
export async function rebuildAll(redis: RedisClientType) {
  const rows = await prismaReadonly.$queryRaw<{ customer_id: number; film_ids: number[] }[]>`
    SELECT c.customer_id,
           coalesce(array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL), '{}') AS film_ids
    FROM customer c
    LEFT JOIN rental r    ON r.customer_id = c.customer_id
    LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
    GROUP BY c.customer_id`;
  const pipeline = redis.multi();
  for (const row of rows) queueReplace(pipeline, row.customer_id, row.film_ids);
  // execAsPipeline sends everything in one round trip without wrapping it in MULTI/EXEC.
  // Each RENAME is atomic on its own, which is all a reader needs.
  await pipeline.execAsPipeline();
  return rows.length;
}

// missing: film ids PostgreSQL has and Redis does not. extra: the other way round.
// orphan: a set for a customer PostgreSQL does not have.
export type Mismatch = { key: string; missing: string[]; extra: string[]; orphan: boolean };

// Members are strings in Redis: sort "9" before "10".
const byNumber = (a: string, b: string) => a.length - b.length || a.localeCompare(b);

// Compares the members of every set with PostgreSQL, and looks for sets no customer explains.
export async function verify(redis: RedisClientType) {
  const rows = await prismaReadonly.$queryRaw<{ customer_id: number; film_ids: number[] }[]>`
    SELECT c.customer_id,
           coalesce(array_agg(DISTINCT i.film_id) FILTER (WHERE i.film_id IS NOT NULL), '{}') AS film_ids
    FROM customer c
    LEFT JOIN rental r    ON r.customer_id = c.customer_id
    LEFT JOIN inventory i ON i.inventory_id = r.inventory_id
    GROUP BY c.customer_id
    ORDER BY c.customer_id`;
  const expected = new Map(rows.map((row) => [filmsKey(row.customer_id), new Set(row.film_ids.map(String))]));

  const pipeline = redis.multi();
  for (const key of expected.keys()) pipeline.sMembers(key);
  const actual = (await pipeline.execAsPipeline()) as unknown as string[][]; // one round trip

  const mismatches: Mismatch[] = [];
  [...expected].forEach(([key, want], i) => {
    const have = new Set(actual[i]);
    const missing = [...want].filter((id) => !have.has(id)).sort(byNumber);
    const extra = [...have].filter((id) => !want.has(id)).sort(byNumber);
    if (missing.length || extra.length) mismatches.push({ key, missing, extra, orphan: false });
  });

  // SCAN walks the keys in batches; KEYS would block Redis while it runs.
  for await (const keys of redis.scanIterator({ MATCH: "customer:*:films", COUNT: 1000 })) {
    for (const key of keys) {
      if (!expected.has(key)) {
        mismatches.push({ key, missing: [], extra: (await redis.sMembers(key)).sort(byNumber), orphan: true });
      }
    }
  }
  return { checked: rows.length, mismatches };
}

export async function disconnectAll() {
  await Promise.all([prisma.$disconnect(), prismaReadonly.$disconnect()]);
}
