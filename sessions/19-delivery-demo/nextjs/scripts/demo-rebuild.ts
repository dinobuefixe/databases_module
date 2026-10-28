// Demo 2: lose every Redis key, rebuild from PostgreSQL, verify.
// The tutorial says FLUSHALL. The course's Redis is shared by every project, so this empties
// only logical database 3 with FLUSHDB. In your own project, FLUSHALL is the real rehearsal.
import "dotenv/config";
import { rebuildAll, verify } from "@/lib/films-sets";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

async function main() {
  const redis = await getRedis();
  const report = async (label: string) => {
    const { checked, mismatches } = await verify(redis);
    console.log(`${label.padEnd(16)} keys=${String(await redis.dbSize()).padStart(5)}  ${checked} customers checked, ${mismatches} mismatches  ${mismatches ? "FAIL" : "OK"}`);
    return mismatches;
  };

  await report("before");
  await redis.flushDb();
  await report("after FLUSHDB");

  const started = performance.now();
  const customers = await rebuildAll(redis);
  console.log(`rebuild          ${customers} customers in ${Math.round(performance.now() - started)} ms (one query, one pipeline)`);

  const mismatches = await report("after rebuild");
  await redis.quit();
  process.exitCode = mismatches ? 1 : 0;
}

main().finally(() => prisma.$disconnect());
