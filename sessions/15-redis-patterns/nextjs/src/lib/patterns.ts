import { randomUUID } from "node:crypto";
import type { RedisClientType } from "redis";

// Deletes the lock only if it still holds our token. GET and DEL run inside Redis as one step,
// so no other client can take the lock between the check and the delete.
const RELEASE = `
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
`;

// Runs job only if nobody else holds lock:<name>. Returns false without running it otherwise.
export async function runExclusively(
  redis: RedisClientType,
  name: string,
  job: () => Promise<void>,
  ttlSeconds = 60,
): Promise<boolean> {
  const key = `lock:${name}`;
  const token = randomUUID();
  // SET key token NX EX ttl: only one client gets OK; the key expires if that client crashes.
  const acquired = await redis.set(key, token, { condition: "NX", expiration: { type: "EX", value: ttlSeconds } });
  if (acquired !== "OK") return false;
  try {
    await job();
  } finally {
    await redis.eval(RELEASE, { keys: [key], arguments: [token] });
  }
  return true;
}

// Fixed-window rate limit: one counter per client per minute.
export async function allowRequest(redis: RedisClientType, clientId: string, limit = 10) {
  const window = Math.floor(Date.now() / 1000 / 60);
  const key = `ratelimit:${clientId}:${window}`;
  // MULTI/EXEC: INCR and EXPIRE are sent together and run together.
  const [count] = await redis.multi().incr(key).expire(key, 60).exec();
  return { allowed: Number(count) <= limit, count: Number(count), limit };
}
