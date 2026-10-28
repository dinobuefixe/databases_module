// Rebuilds every customer:{id}:films set from PostgreSQL.
//   npm run rebuild        one query per customer (the tutorial's first version)
//   npm run rebuild:fast   one query and one pipeline
import "dotenv/config";
import { disconnectAll, rebuildAll, rebuildPerCustomer } from "@/lib/films-sets";
import { getRedis } from "@/lib/redis";

async function main() {
  const fast = process.argv.includes("--fast");
  const redis = await getRedis();
  const started = performance.now();
  const customers = fast ? await rebuildAll(redis) : await rebuildPerCustomer(redis);
  const ms = Math.round(performance.now() - started);
  console.log(`${fast ? "single query + pipeline" : "per customer"}: rebuilt ${customers} customers in ${ms} ms`);
  await redis.quit();
  await disconnectAll();
}

main();
