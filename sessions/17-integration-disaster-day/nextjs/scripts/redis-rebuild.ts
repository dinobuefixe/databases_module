// Restores Redis by rebuilding every derived key from PostgreSQL. Redis holds nothing else.
import "dotenv/config";
import { rebuildAll } from "@/lib/films-sets";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

async function main() {
  const redis = await getRedis();
  const started = performance.now();
  const customers = await rebuildAll(redis);
  console.log(`Rebuilt customer:{id}:films for ${customers} customers in ${Math.round(performance.now() - started)} ms`);
  await redis.quit();
  await prisma.$disconnect();
}

main();
