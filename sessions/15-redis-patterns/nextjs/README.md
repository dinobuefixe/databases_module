# Session 15 in Next.js with Prisma: Redis data structures and patterns

The session 15 tutorial with the official `redis` client: a counter, a hash, a set of daily visitors and a sorted set of search terms, then cache-aside for a Pagila customer, a lock with safe release in Lua, and a fixed-window rate limit.

| File | What it shows |
|------|---------------|
| `src/app/api/films/[id]/views/route.ts` | `INCR film:{id}:views`. |
| `src/app/api/films/[id]/hash/route.ts` | `HSET film:{id} title ... rate ...` with the values from PostgreSQL, and `HGETALL`. |
| `src/app/api/visitors/route.ts` | `SADD visitors:{date} customer:{id}` and `SCARD`. |
| `src/app/api/search/route.ts` | `ZINCRBY search:terms 1 <term>` on every search; the endpoint is rate limited. |
| `src/app/api/search/popular/route.ts` | `ZRANGE search:terms 0 4 REV WITHSCORES`. |
| `src/app/api/customers/[id]/route.ts` | Cache-aside: `GET` answers `"hit"` or `"miss"`; `PATCH` updates PostgreSQL and deletes `cache:customer:{id}`. |
| `src/lib/patterns.ts` | `runExclusively` (`SET ... NX EX` and the Lua release script) and `allowRequest` (`INCR` and `EXPIRE` in `MULTI`/`EXEC`). |
| `scripts/lock-demo.ts`, `scripts/lock-worker.ts` | `npm run lock-demo`: two processes start together; only one runs the job. |
| `src/lib/redis.ts` | One shared connection to Redis logical database 3. |

| redis-py | node-redis |
|----------|------------|
| `r.set(k, v, nx=True, ex=30)` | `redis.set(k, v, { condition: "NX", expiration: { type: "EX", value: 30 } })` |
| `r.register_script(lua)(keys=..., args=...)` | `redis.eval(lua, { keys: [...], arguments: [...] })` |
| `r.pipeline()` (transactional by default) | `redis.multi()...exec()` |
| `r.zrange(k, 0, 4, desc=True, withscores=True)` | `redis.zRangeWithScores(k, 0, 4, { REV: true })` |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s15_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run lock-demo
npm run dev
```

```bash
curl -X POST localhost:3000/api/films/42/views                       # {"views": 1}, then 2, 3...
curl -X PUT localhost:3000/api/films/42/hash
curl localhost:3000/api/films/42/hash
curl -X POST localhost:3000/api/visitors -H 'content-type: application/json' -d '{"customer_id": 5}'
curl -X POST localhost:3000/api/visitors -H 'content-type: application/json' -d '{"customer_id": 9}'
curl -X POST localhost:3000/api/visitors -H 'content-type: application/json' -d '{"customer_id": 5}'   # "added": 0, "unique": 2
curl 'localhost:3000/api/search?q=alien'
curl 'localhost:3000/api/search?q=matrix'
curl localhost:3000/api/search/popular
curl localhost:3000/api/customers/5                                   # "cache": "miss"
curl localhost:3000/api/customers/5                                   # "cache": "hit", "ttl" counting down
curl -X PATCH localhost:3000/api/customers/5 -H 'content-type: application/json' -d '{"first_name": "LIZ"}'
curl localhost:3000/api/customers/5                                   # "miss" again, with the new name
```

Rate limit: the 11th search in the same minute from the same client gets `429`.

```bash
for i in $(seq 1 11); do curl -s -o /dev/null -w "%{http_code} " 'localhost:3000/api/search?q=x' -H 'x-client-id: me'; done
```

To look at the keys directly:

```bash
docker compose exec redis redis-cli -a change-me-redis -n 3 --no-auth-warning
```

All the Next.js projects use logical database 3, so you may see keys from other sessions there.

## Things to try

- Run `npm run lock-demo` and, while it runs, `TTL lock:nightly-export` in `redis-cli`. Then change the job in `scripts/lock-worker.ts` to wait 70 seconds (longer than the lock's 60): a third worker started after 60 seconds gets the lock too. The Lua release stops the first worker from deleting the third one's lock when it finishes.
- Replace the Lua release with a plain `redis.del(key)` and work out the sequence of events in which it deletes someone else's lock.
- Update customer 5 directly in `psql` instead of through `PATCH`. The API keeps answering with the old name until the TTL runs out. This is why every write path must delete the key.
- Fire 100 concurrent `POST /api/films/7/views` requests (`seq 100 | xargs -P20 -I{} curl -s -o /dev/null -X POST localhost:3000/api/films/7/views`) and check the counter is exactly 100.
- Send 10 searches at the end of a minute and 10 more at the start of the next: all 20 pass. That is the weakness of a fixed window.
