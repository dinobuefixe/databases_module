// Sends ZINCRBY to this week's leaderboard as fast as it can, then prints the rate and the top 10.
// Usage: npm run leaderboard-load -- [--seconds 5] [--batch 100]
//
// Each batch goes in one multi() sent with execAsPipeline(): one round trip, no MULTI/EXEC.
// Other clients' commands may run between the increments, which is fine because each ZINCRBY
// is atomic on its own. --batch 1 sends one command per round trip, for comparison.
import "dotenv/config";
import { LEADERBOARD_TTL, leaderboardKey } from "@/lib/leaderboard";
import { getRedis } from "@/lib/redis";

function option(name: string, fallback: number): number {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? fallback : Number(process.argv[i + 1]);
}

async function main() {
  const seconds = option("seconds", 5);
  const batch = option("batch", 100);
  const redis = await getRedis();
  const key = leaderboardKey();

  let updates = 0;
  const start = performance.now();
  while (performance.now() - start < seconds * 1000) {
    const pipe = redis.multi();
    for (let i = 0; i < batch; i++) {
      // 999 ** random() is between 1 and 999 but mostly small, so a few customers rent a lot;
      // * 337 % 999 shuffles which ids those are, so the top 10 is not just ids 1 to 10.
      const customerId = ((Math.floor(999 ** Math.random()) * 337) % 999) + 1;
      pipe.zIncrBy(key, 1, `customer:${customerId}`);
    }
    pipe.expire(key, LEADERBOARD_TTL, "NX");
    await pipe.execAsPipeline();
    updates += batch;
  }
  const elapsed = (performance.now() - start) / 1000;

  const rate = Math.round(updates / elapsed).toLocaleString("en-GB");
  console.log(`${updates.toLocaleString("en-GB")} ZINCRBY in ${elapsed.toFixed(1)} s: ${rate} updates per second (batch ${batch})`);
  console.log(`${key}: ${await redis.zCard(key)} customers, TTL ${await redis.ttl(key)} s`);
  const top = await redis.zRangeWithScores(key, 0, 9, { REV: true });
  top.forEach(({ value, score }, i) => console.log(`${String(i + 1).padStart(3)}. ${value.padEnd(14)} ${String(score).padStart(8)}`));
  const rank = await redis.zRevRank(key, "customer:500");
  if (rank !== null) console.log(`customer:500 is number ${rank + 1} with ${await redis.zScore(key, "customer:500")}`);
  await redis.quit();
}

main();
