// Empties this project's Redis logical database, to rehearse losing every derived key.
// The tutorial says FLUSHALL, which empties every logical database on the server. On the shared
// course server that would delete other projects' keys, so we use FLUSHDB on database 3 only.
import "dotenv/config";
import { getRedis } from "@/lib/redis";

async function main() {
  const redis = await getRedis();
  const before = await redis.dbSize();
  await redis.flushDb();
  console.log(`FLUSHDB: removed ${before} keys from ${process.env.REDIS_URL?.replace(/:[^:@]*@/, ":***@")}`);
  await redis.quit();
}

main();
