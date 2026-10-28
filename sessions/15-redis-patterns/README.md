# Session 15: Redis data structures and patterns

The tutorial from [session 15](../../README.md#session-15-redis-i-data-structures-and-patterns), written three times as independent projects.

Each Redis structure from the tutorial behind an endpoint (counter, hash, set, sorted set), then cache-aside for a Pagila customer with invalidation on update, a lock with safe release in Lua, and a fixed-window rate limit that answers 429.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `redis-py` | 8000 |
| [django](django/) | `redis-py` | 8001 |
| [nextjs](nextjs/) | `redis` (node-redis) | 3000 |

Call the customer endpoint twice and then update it: each response says whether it came from the cache.
