// Change a customer's username only if the new one is free, with two techniques from the tutorial.
// Keys: "usernames" (a set of every username taken) and "customer:{id}" (a hash with the username).
import { WatchError, type RedisClientType } from "redis";

// Optimistic locking: WATCH the keys, read, then MULTI/EXEC. If another client changed a watched
// key in between, EXEC fails with WatchError and we try again with fresh values.
export async function changeWithWatch(redis: RedisClientType, customerId: number, username: string) {
  const customerKey = `customer:${customerId}`;
  // WATCH belongs to a connection. The shared connection also carries other requests' commands,
  // so this takes a connection of its own.
  const conn = redis.duplicate();
  await conn.connect();
  try {
    for (let attempt = 1; ; attempt++) {
      try {
        await conn.watch(["usernames", customerKey]);
        const old = await conn.hGet(customerKey, "username");
        if (old === username) {
          await conn.unwatch();
          return { changed: true, attempts: attempt };
        }
        if (await conn.sIsMember("usernames", username)) {
          await conn.unwatch();
          return { changed: false, attempts: attempt };
        }
        const multi = conn.multi();
        if (old) multi.sRem("usernames", old);
        multi.sAdd("usernames", username);
        multi.hSet(customerKey, "username", username);
        await multi.exec();
        return { changed: true, attempts: attempt };
      } catch (err) {
        if (!(err instanceof WatchError)) throw err;
      }
    }
  } finally {
    conn.destroy();
  }
}

// The same logic as a Lua script: Redis runs it in one step, so nothing can change in the middle
// and there is nothing to retry. It reads the old name itself instead of receiving it.
const CHANGE = `
if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 1 then
    return redis.call('HGET', KEYS[2], 'username') == ARGV[1] and 1 or 0
end
local old = redis.call('HGET', KEYS[2], 'username')
if old then redis.call('SREM', KEYS[1], old) end
redis.call('SADD', KEYS[1], ARGV[1])
redis.call('HSET', KEYS[2], 'username', ARGV[1])
return 1
`;

export async function changeWithLua(redis: RedisClientType, customerId: number, username: string) {
  const result = await redis.eval(CHANGE, { keys: ["usernames", `customer:${customerId}`], arguments: [username] });
  return { changed: result === 1, attempts: 1 };
}
