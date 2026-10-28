// Exit code 0 when every customer:{id}:films set matches PostgreSQL, 1 otherwise.
import "dotenv/config";
import { verify } from "@/lib/films-sets";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

async function main() {
  const redis = await getRedis();
  const { checked, mismatches } = await verify(redis);
  for (const m of mismatches.slice(0, 10)) {
    console.error(`customer ${m.customer_id}: redis=${m.redis} postgres=${m.postgres}`);
  }
  console.log(`redis: ${checked} customers checked, ${mismatches.length} mismatches`);
  await redis.quit();
  await prisma.$disconnect();
  process.exitCode = mismatches.length ? 1 : 0;
}

main();
