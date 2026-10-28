import { createClient, type RedisClientType } from "redis";

const globalForRedis = globalThis as unknown as { redis?: Promise<RedisClientType> };

export function getRedis(): Promise<RedisClientType> {
  if (!globalForRedis.redis) {
    const client: RedisClientType = createClient({
      url: process.env.REDIS_URL ?? "redis://:change-me-redis@localhost:6379/3",
    });
    client.on("error", (err) => console.error("Redis error", err));
    globalForRedis.redis = client.connect().then(() => client);
  }
  return globalForRedis.redis;
}
