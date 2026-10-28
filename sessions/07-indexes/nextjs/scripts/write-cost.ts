import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { INDEXES } from "./indexes";

// Measure what indexes cost on writes: insert 100,000 rows into big_rental
// with no index, with the composite index, and with both, as in the tutorial.
// Each insert runs in a transaction that is rolled back, so the table does
// not grow. The indexes present at the start are restored at the end.
class Rollback extends Error {}

async function timeInsert(): Promise<number> {
  let ms = 0;
  try {
    await prisma.$transaction(
      async (tx) => {
        const start = performance.now();
        await tx.$executeRaw`
          INSERT INTO big_rental
          SELECT g, 1, now(), NULL FROM generate_series(2000001, 2100000) g`;
        ms = performance.now() - start;
        throw new Rollback();
      },
      { timeout: 120_000 },
    );
  } catch (err) {
    if (!(err instanceof Rollback)) throw err;
  }
  return ms;
}

async function main() {
  const existing = await prisma.$queryRaw<{ indexname: string }[]>`
    SELECT indexname FROM pg_indexes WHERE tablename = 'big_rental'`;
  const had = new Set(existing.map((r) => r.indexname));

  await INDEXES.composite.drop();
  await INDEXES.partial.drop();
  await INDEXES.single.drop(); // not part of the measurement
  console.log(`no indexes                    ${(await timeInsert()).toFixed(0).padStart(6)} ms`);

  await INDEXES.composite.create();
  console.log(`composite                     ${(await timeInsert()).toFixed(0).padStart(6)} ms`);

  await INDEXES.partial.create();
  console.log(`composite + partial           ${(await timeInsert()).toFixed(0).padStart(6)} ms`);

  // Put things back as they were.
  if (!had.has("big_rental_customer_rented")) await INDEXES.composite.drop();
  if (!had.has("big_rental_open")) await INDEXES.partial.drop();
  if (had.has("big_rental_rented")) await INDEXES.single.create();
}

main().finally(() => prisma.$disconnect());
