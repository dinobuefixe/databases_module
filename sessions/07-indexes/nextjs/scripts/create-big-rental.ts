import "dotenv/config";
import { prisma } from "@/lib/prisma";

// Creates the tutorial's big_rental table, reproducible with setseed(0.1).
// Usage: npm run big-rental -- [rows]      (default 2000000)
const rows = Number(process.argv[2] ?? 2_000_000);

async function main() {
  const start = performance.now();
  // setseed and CREATE TABLE must share a connection: one interactive transaction.
  await prisma.$transaction(
    async (tx) => {
      await tx.$executeRaw`DROP TABLE IF EXISTS big_rental`;
      await tx.$executeRaw`SELECT setseed(0.1)`;
      await tx.$executeRaw`
        CREATE TABLE big_rental AS
        SELECT g AS id,
               (random() * 599 + 1)::int                 AS customer_id,
               now() - random() * interval '3 years'      AS rented_at,
               CASE WHEN random() < 0.03 THEN NULL ELSE now() END AS returned_at
        FROM generate_series(1, ${rows}::int) AS g`;
    },
    { timeout: 600_000 },
  );
  // VACUUM cannot run inside a transaction, so it runs on its own afterwards. It marks the new
  // pages all-visible (as autovacuum would do a little later); ANALYZE gives fresh statistics.
  await prisma.$executeRaw`VACUUM ANALYZE big_rental`;
  const [{ count, size }] = await prisma.$queryRaw<{ count: number; size: string }[]>`
    SELECT count(*)::int AS count, pg_size_pretty(pg_table_size('big_rental')) AS size FROM big_rental`;
  console.log(`big_rental: ${count} rows, ${size}, in ${((performance.now() - start) / 1000).toFixed(1)} s (no indexes)`);
}

main().finally(() => prisma.$disconnect());
