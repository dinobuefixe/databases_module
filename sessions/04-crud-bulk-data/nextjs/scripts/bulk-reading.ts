import "dotenv/config";
import { prisma } from "@/lib/prisma";

// The tutorial's bulk load in SQL: generate_series with a fixed seed.
// Usage: npm run bulk:reading -- [rows]     (default 1000000)
const rows = Number(process.argv[2] ?? 1_000_000);

async function main() {
  const start = performance.now();
  // setseed only affects the current session, so both statements must run on
  // the same connection: an interactive transaction guarantees that.
  await prisma.$transaction(
    async (tx) => {
      await tx.$executeRaw`DROP TABLE IF EXISTS reading`;
      // $executeRaw because setseed returns void, which $queryRaw cannot deserialise.
      await tx.$executeRaw`SELECT setseed(0.42)`;
      await tx.$executeRaw`
        CREATE TABLE reading AS
        SELECT g AS reading_id,
               now() - random() * interval '365 days' AS taken_at,
               round((random() * 100)::numeric, 2)    AS value
        FROM generate_series(1, ${rows}::int) AS g`;
    },
    { timeout: 300_000 },
  );
  const seconds = ((performance.now() - start) / 1000).toFixed(2);

  // Same seed, same values: this sum is identical on every run.
  const [stats] = await prisma.$queryRaw<{ count: bigint; total: string }[]>`
    SELECT count(*), sum(value)::text AS total FROM reading`;
  console.log(`reading: ${stats.count} rows in ${seconds} s, sum(value) = ${stats.total}`);
}

main().finally(() => prisma.$disconnect());
