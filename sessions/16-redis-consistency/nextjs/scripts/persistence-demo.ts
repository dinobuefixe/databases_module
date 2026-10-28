// Kills Redis in the middle of a stream of writes and counts how many survived.
//   npm run persistence-demo
// It INCRs a counter as fast as it can, runs `docker compose kill redis` after two seconds (SIGKILL:
// Redis gets no chance to save anything), starts Redis again and compares the last value Redis
// acknowledged with the value it loaded from disk. Run it with the default server (RDB snapshots only)
// and again with AOF on; the README shows how to switch.
// Killing the container stops Redis for a few seconds for every project that uses it.
import "dotenv/config";
import { execFileSync, spawn } from "node:child_process";
import path from "node:path";
import { createClient } from "redis";

const REPO_ROOT = path.resolve(__dirname, "../../../.."); // the folder with docker-compose.yml
const WRITE_FOR_MS = 2000; // writes before the kill

const compose = (...args: string[]) => ["compose", "--project-directory", REPO_ROOT, ...args];
const clock = (date: Date) => date.toTimeString().slice(0, 8);

// No reconnects and no offline queue: when Redis dies, the next INCR must fail at once instead of
// waiting for Redis to come back and then succeeding.
async function connect() {
  const client = createClient({ url: process.env.REDIS_URL, disableOfflineQueue: true, socket: { reconnectStrategy: false } });
  client.on("error", () => {}); // the kill is expected; the failed command reports it
  await client.connect();
  return client;
}

async function waitForRedis(timeoutMs = 60_000) {
  const started = performance.now();
  for (;;) {
    let client: Awaited<ReturnType<typeof connect>> | undefined;
    try {
      client = await connect();
      await client.ping(); // fails with LOADING while Redis is still reading its files
      return { client, waited: performance.now() - started };
    } catch (err) {
      client?.destroy();
      if (performance.now() - started > timeoutMs) throw err;
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
  }
}

async function main() {
  let redis = await connect();
  const config = await redis.configGet(["appendonly", "appendfsync"]);
  const aof = config.appendonly === "yes";
  console.log(`Persistence: ${aof ? `AOF, appendfsync ${config.appendfsync}` : "RDB snapshots only (appendonly no)"}`);

  // A new key per run, so a snapshot from an earlier run cannot already hold it.
  for await (const keys of redis.scanIterator({ MATCH: "persistence-demo:*" })) {
    if (keys.length) await redis.del(keys);
  }
  const key = `persistence-demo:${Math.floor(Date.now() / 1000)}`;

  let acknowledged = 0;
  let killed: Promise<unknown> | undefined;
  let lastSave = new Date();
  const startedAt = new Date();
  const started = performance.now();
  try {
    for (;;) {
      // The reply is the new value, so Redis has applied every write up to it.
      acknowledged = await redis.incr(key);
      if (!killed && performance.now() - started >= WRITE_FOR_MS) {
        lastSave = new Date((await redis.lastSave()) * 1000);
        // spawn does not wait: the loop keeps writing until the kill lands.
        const killer = spawn("docker", compose("kill", "redis"), { stdio: "ignore" });
        killed = new Promise((resolve) => killer.on("exit", resolve));
      }
    }
  } catch {
    // Redis is gone.
  }
  await killed;
  redis.destroy();

  console.log(`Writes acknowledged before the kill: ${acknowledged}`);
  if (!aof) console.log(`Writes started at ${clock(startedAt)}; last RDB snapshot before the kill: ${clock(lastSave)}`);

  execFileSync("docker", compose("start", "redis"), { stdio: "ignore" });
  const back = await waitForRedis();
  redis = back.client;
  console.log(`Redis answers again after ${(back.waited / 1000).toFixed(1)} s`);

  const survived = Number((await redis.get(key)) ?? 0);
  const lost = Math.max(acknowledged - survived, 0);
  console.log(`Counter after the restart: ${survived}`);
  console.log(`Lost: ${lost} writes (${Math.round((100 * lost) / acknowledged)}%)`);
  redis.destroy();
}

main();
