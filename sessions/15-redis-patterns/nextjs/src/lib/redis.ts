import { createClient, type RedisClientType } from "redis";

const globalForRedis = globalThis as unknown as { redis?: Promise<RedisClientType> };

// Connect once and share the connection between requests.
export function getRedis(): Promise<RedisClientType> {
  if (!globalForRedis.redis) {
    const client: RedisClientType = createClient({ url: process.env.REDIS_URL });
    client.on("error", (err) => console.error("Redis error", err));
    globalForRedis.redis = client.connect().then(() => client);
  }
  return globalForRedis.redis;
}
