# Session 16 in Next.js with Prisma: source of truth, rebuild and persistence

Keeps a Redis set per customer with the films they have rented (`customer:{id}:films`), derived from PostgreSQL. It rebuilds the sets with a temporary key and `RENAME`, verifies them with an exit code, reads the server's persistence settings and changes usernames with `WATCH` and with Lua, as in the session 16 tutorial.

| File | What it shows |
|------|---------------|
| `src/lib/films-sets.ts` | `rebuildPerCustomer` (one query per customer), `rebuildAll` (one query, one pipeline) and `verify`. |
| `scripts/flush.ts` | `npm run flush`: `FLUSHDB` on this project's Redis database (see below). |
| `scripts/rebuild.ts` | `npm run rebuild` and `npm run rebuild:fast`, with timings. |
| `scripts/verify.ts` | `npm run verify`: exits 0 when every set matches PostgreSQL, 1 otherwise. |
| `src/app/api/verify/route.ts` | The same check over HTTP: 200 or 409. |
| `src/app/api/customers/[id]/films/route.ts` | Reads one derived set. |
| `src/app/api/redis/persistence/route.ts` | `CONFIG GET` for `appendonly`, `appendfsync`, `save`, `maxmemory`, `maxmemory-policy`. |
| `src/lib/usernames.ts` | `WATCH` + `MULTI`/`EXEC` with retries on a dedicated connection, and the Lua version. |
| `src/app/api/customers/[id]/username/route.ts` | `PUT` with `"method": "watch"` or `"lua"`; 409 when the name is taken. |

Source of truth for each piece of data in this project:

| Data | Where | Kind | If lost |
|------|-------|------|---------|
| customers, rentals, inventory | PostgreSQL | source of truth | restore from backup |
| `customer:{id}:films` | Redis | derived | `npm run rebuild:fast` |
| `usernames`, `customer:{id}` hash | Redis | source of truth in this demo | lost; in a real app the username would live in PostgreSQL and these keys would be derived from it |

## FLUSHDB instead of FLUSHALL

The tutorial empties Redis with `FLUSHALL`, which deletes every key in every logical database on the server. The course's Redis is shared: the FastAPI, Django and Next.js projects use databases 1, 2 and 3. `npm run flush` runs `FLUSHDB` while connected to database 3, which empties only this project's keys. In your group project, with a Redis of your own, `FLUSHALL` is the honest rehearsal of losing Redis.

## Recommended persistence settings

`/api/redis/persistence` shows what the course server uses: RDB snapshots (`save 3600 1 300 100 60 10000`), no AOF, no memory limit. Changing them at runtime with `CONFIG SET` is not allowed on the shared server; set them where Redis starts. For this project:

```yaml
# docker-compose.yml
  redis:
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}",
              "--appendonly", "yes", "--appendfsync", "everysec",
              "--maxmemory", "256mb", "--maxmemory-policy", "noeviction"]
```

- `appendonly yes` with `appendfsync everysec`: at most about one second of writes is lost on a crash. The usernames here are not derived, so they need it.
- `maxmemory-policy noeviction`: when memory is full, writes fail with an error instead of Redis silently dropping keys. With `allkeys-lru` a film set could disappear and `verify` would fail with nobody having deleted anything. Use `allkeys-lru` for a Redis that only holds a cache.
- If every key were derived, you could turn persistence off and rebuild after each restart.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s16_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run verify         # exit code 1: the sets do not exist yet
npm run rebuild        # per customer: ~1,000 queries, about a second
npm run verify         # 0 mismatches, exit code 0
npm run flush          # lose every key in database 3
npm run rebuild:fast   # one query and one pipeline, tens of milliseconds
npm run verify
npm run dev
```

```bash
curl localhost:3000/api/customers/1/films
curl localhost:3000/api/verify
curl localhost:3000/api/redis/persistence
curl -X PUT localhost:3000/api/customers/5/username -H 'content-type: application/json' -d '{"username": "ana", "method": "watch"}'
curl -X PUT localhost:3000/api/customers/6/username -H 'content-type: application/json' -d '{"username": "ana", "method": "lua"}'   # 409
```

## Things to try

- Delete one set in `redis-cli` (`DEL customer:7:films`) or add a member to it, then run `npm run verify` and `echo $?`.
- Insert a rental for customer 1 in `psql`. `verify` now fails for that customer until you rebuild: writing to PostgreSQL does not update Redis on its own.
- Twenty customers race for the same username; exactly one gets it, with either method:

  ```bash
  seq 100 119 | xargs -P20 -I{} curl -s -o /dev/null -w "%{http_code}\n" -X PUT localhost:3000/api/customers/{}/username \
      -H 'content-type: application/json' -d '{"username": "zed", "method": "watch"}' | sort | uniq -c
  ```

- Twenty customers change to twenty different names at once with `"method": "watch"` and look at `attempts` in the responses. Every change touches `usernames`, so most transactions are aborted and retried. The Lua version never retries.
- Run `npm run rebuild` while calling `/api/customers/1/films` in a loop: thanks to `RENAME` the count never drops to a partial value.
