// One command from a clean clone to a ready demo: migrations, big_rental, Redis sets.
// Safe to run again: each step skips what is already there.
import "dotenv/config";
import { execSync } from "node:child_process";
import { rebuildAll } from "@/lib/films-sets";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

const run = (cmd: string) => execSync(cmd, { stdio: "inherit" });

async function exists(table: string) {
  const [row] = await prisma.$queryRaw<{ found: boolean }[]>`SELECT to_regclass(${table}) IS NOT NULL AS found`;
  return row.found;
}

async function main() {
  console.log("1/3 Migrations");
  if (!(await exists("_prisma_migrations"))) run("npx prisma migrate resolve --applied 0_init");
  run("npx prisma migrate deploy");

  console.log("2/3 big_rental (session 07)");
  if (await exists("big_rental")) {
    console.log("big_rental already exists");
  } else {
    const rows = Number(process.env.BIG_RENTAL_ROWS ?? 2_000_000);
    const started = performance.now();
    // setseed and the INSERT must run on the same connection, so they share a transaction.
    await prisma.$transaction(
      async (tx) => {
        await tx.$executeRaw`CREATE TABLE big_rental (id int, customer_id int, rented_at timestamptz, returned_at timestamptz)`;
        await tx.$executeRaw`SELECT setseed(0.1)`; // $executeRaw: setseed returns void, which $queryRaw cannot map
        await tx.$executeRaw`
          INSERT INTO big_rental
          SELECT g, (random() * 599 + 1)::int, now() - random() * interval '3 years',
                 CASE WHEN random() < 0.03 THEN NULL ELSE now() END
          FROM generate_series(1, ${rows}::int) AS g`;
      },
      { timeout: 300_000 },
    );
    // VACUUM marks the new pages all-visible so the partial index can be read with an index-only scan.
    await prisma.$executeRaw`VACUUM ANALYZE big_rental`;
    console.log(`Created big_rental with ${rows} rows in ${Math.round(performance.now() - started)} ms`);
  }

  console.log("3/3 Redis sets (session 16)");
  const redis = await getRedis();
  console.log(`Rebuilt customer:{id}:films for ${await rebuildAll(redis)} customers`);
  await redis.quit();
}

main().finally(() => prisma.$disconnect());
