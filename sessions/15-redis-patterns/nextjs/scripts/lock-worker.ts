// One worker that tries to run the nightly export under the Redis lock.
// Usage: tsx scripts/lock-worker.ts <worker-name>
import "dotenv/config";
import { runExclusively } from "@/lib/patterns";
import { getRedis } from "@/lib/redis";

const worker = process.argv[2] ?? `worker-${process.pid}`;

async function main() {
  const redis = await getRedis();
  const ran = await runExclusively(redis, "nightly-export", async () => {
    console.log(`${worker}: got the lock, exporting... (TTL ${await redis.ttl("lock:nightly-export")}s)`);
    await new Promise((resolve) => setTimeout(resolve, 2000)); // the "job"
    console.log(`${worker}: done, releasing the lock`);
  });
  if (!ran) console.log(`${worker}: lock:nightly-export is held by another worker, skipping`);
  await redis.quit();
}

main();
