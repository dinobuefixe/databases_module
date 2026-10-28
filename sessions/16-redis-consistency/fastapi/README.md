# Session 16 in FastAPI: source of truth, rebuild and persistence

Keeps a Redis set per customer with the films they have rented (`customer:{id}:films`), rebuilds every set from PostgreSQL in two ways, verifies Redis against PostgreSQL with an exit code, kills Redis in the middle of a stream of writes to compare RDB with AOF, backs Redis up and restores it, and changes a username atomically with `WATCH` and with Lua.

| File | What it shows |
|------|---------------|
| `app/films_sets.py` | `rebuild_customer` (one query per customer, temp key + `RENAME`), `rebuild_single_query` (one query, one pipeline), `verify` (every set compared member by member with PostgreSQL, plus a `SCAN` for sets of customers that do not exist). |
| `scripts/rebuild.py` | Runs one or both rebuilds with timings. `--flush` empties this project's Redis database first with `FLUSHDB`. |
| `scripts/verify.py` | Prints the differences and exits 0 (agree) or 1 (differ). |
| `scripts/persistence_demo.py` | Writes in a loop, kills Redis with `docker compose kill redis`, starts it again and reports how many writes survived. |
| `scripts/seed_usernames.py` | Fills the `usernames` set and the `customer:{id}` hashes used by the username example. |
| `app/usernames.py` | `change_username_watch` (optimistic locking with `WATCH`/`MULTI`/`EXEC` and a retry loop) and `change_username_lua` (the same in one script). Both read the old name inside the transaction. |
| `app/main.py` | `GET /verify`, `GET /customers/{id}/films`, `GET /redis/persistence`, `PUT /customers/{id}/username`. |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s16_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python -m scripts.verify; echo $?          # Redis is empty: 997 keys differ, exit 1
uv run python -m scripts.rebuild --flush          # per-customer about 1.2 s, single about 0.05 s
uv run python -m scripts.verify; echo $?          # OK, exit 0
uv run python -m scripts.seed_usernames
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

The first `verify` reports 997 keys, not 999, because two customers have no rentals: their set should be empty, and a missing key already counts as empty (`SMEMBERS` returns an empty set).

```bash
curl localhost:8000/verify                 # {"ok": true, ...}
curl localhost:8000/customers/1/films
curl localhost:8000/redis/persistence
curl -X PUT localhost:8000/customers/1/username -H 'content-type: application/json' -d '{"username": "mary.s"}'
curl -X PUT localhost:8000/customers/2/username -H 'content-type: application/json' -d '{"username": "mary.s", "method": "lua"}'   # 409
```

## FLUSHDB, not FLUSHALL

The tutorial empties Redis with `FLUSHALL`, which deletes the keys of every logical database on the server. In this repository the Redis container is shared: the FastAPI, Django and Next.js projects use databases `/1`, `/2` and `/3`. `--flush` therefore runs `FLUSHDB`, which empties only the database selected in `REDIS_URL`. On a Redis that only your project uses, `FLUSHALL` and `FLUSHDB` give the same result for this exercise. The other FastAPI projects from sessions 15 to 19 also use `/1`, so `--flush` deletes their keys too; they rebuild or recreate them when you run them again.

## Source of truth

| Data | Where it lives | Group | If Redis loses it |
|------|----------------|-------|-------------------|
| Rentals, customers, films | PostgreSQL | Source of truth | Not in Redis |
| `customer:{id}:films` | Redis | Derived | `uv run python -m scripts.rebuild` |
| `usernames`, `customer:{id}` hashes | Redis | Example data for `WATCH`/Lua, seeded from PostgreSQL emails | `uv run python -m scripts.seed_usernames` (changes made through the API are lost) |

## Persistence settings

`GET /redis/persistence` reads the current values with `CONFIG GET`. The repository's `docker-compose.yml` runs Redis with the image defaults: `appendonly no` and RDB snapshots (`save 3600 1 300 100 60 10000`: a snapshot after 3600 s if at least 1 key changed, after 300 s if 100 changed, after 60 s if 10,000 changed), no memory limit and `noeviction`. Set them where the server is defined, not with `CONFIG SET`; turning AOF on, below, is the one exception.

For a Redis that holds the derived sets of this project, the tutorial's configuration is a reasonable choice:

```
appendonly yes            # log every write; restart loses at most about one second
appendfsync everysec
maxmemory 256mb
maxmemory-policy noeviction   # refuse writes when full instead of silently dropping sets
```

In your own `docker-compose.yml`, pass them as arguments:

```yaml
command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}",
          "--appendonly", "yes", "--appendfsync", "everysec",
          "--maxmemory", "256mb", "--maxmemory-policy", "noeviction"]
```

Because the sets can be rebuilt from PostgreSQL in well under a second, losing them costs little. The reason to keep AOF anyway is to avoid serving empty sets between a restart and the rebuild.

### Kill Redis in the middle of a write: RDB, then AOF

`scripts/persistence_demo.py` INCRs a counter as fast as it can, runs `docker compose kill redis` after two seconds, starts Redis again and compares the last value Redis acknowledged with the value it loaded from disk. `kill` sends SIGKILL, so Redis gets no chance to save on the way out, as in a crash.

The Redis container is shared by every project in this repository. The kill stops it for all of them, for about a second, and with RDB it also loses their writes since the last snapshot. Run it when nothing else depends on Redis.

With the default server:

```bash
uv run python -m scripts.persistence_demo
```

```
Persistence: RDB snapshots only (appendonly no)
Writes acknowledged before the kill: 10668
Writes started at 14:24:29; last RDB snapshot before the kill: 14:23:36
Redis answers again after 0.2 s
Counter after the restart: 0
Lost: 10668 writes (100%)
```

Redis restarted from the last snapshot, so every write after it is gone. That includes the `customer:{id}:films` sets if you rebuilt them after that snapshot: `uv run python -m scripts.verify` fails until you run `uv run python -m scripts.rebuild --mode single` again.

Run it again after a minute without writes. The `60 10000` rule then fires during the loop, at the 10,000th change, and only the writes after that snapshot are lost:

```
Persistence: RDB snapshots only (appendonly no)
Writes acknowledged before the kill: 12672
Writes started at 14:32:24; last RDB snapshot before the kill: 14:32:26
Redis answers again after 0.2 s
Counter after the restart: 10295
Lost: 2377 writes (19%)
```

Now turn AOF on. From the root of the repository:

```bash
docker compose exec redis redis-cli -a change-me-redis CONFIG SET appendonly yes
docker compose -f docker-compose.yml -f docker-compose.redis-aof.yml up -d --wait redis
```

The first line makes the running server write its current keys to a new AOF. The second recreates the container with `--appendonly yes --appendfsync everysec` from `docker-compose.redis-aof.yml`, so the setting survives restarts; it takes about six seconds, during which no project can reach Redis. Do not skip the first line: a Redis that starts with `appendonly yes` and finds no AOF starts empty and ignores `dump.rdb`, so every project's keys would be gone.

Run the demo again (here three runs in a row):

```
Persistence: AOF, appendfsync everysec
Writes acknowledged before the kill: 9167
Redis answers again after 0.2 s
Counter after the restart: 9167
Lost: 0 writes (0%)
```

```
Writes acknowledged before the kill: 10695
Counter after the restart: 10695
Lost: 0 writes (0%)
Writes acknowledged before the kill: 11548
Counter after the restart: 11548
Lost: 0 writes (0%)
```

Nothing is lost, not even the last second. Redis hands each write to the operating system before it replies, and SIGKILL stops the Redis process, not the machine, so the operating system still writes the data to the file. `everysec` is how often Redis calls `fsync` to force those writes onto the disk: the one second you can lose is for a power cut or a kernel crash, which `docker compose kill` does not simulate.

Go back to the default, which the other sessions expect. From the root:

```bash
docker compose up -d --wait redis
```

Redis saves a snapshot as it stops and the new container loads it, so no keys are lost. The `appendonlydir/` folder stays in the volume, unused; the `CONFIG SET` step replaces it the next time you turn AOF on.

### Back up Redis and restore it

With the default server, the backup is `dump.rdb`. Ask for a fresh snapshot, check with `LASTSAVE` (the time of the last snapshot, in seconds since 1970) that it has finished, and copy the file out of the container. `backups/` is in `.gitignore`.

```bash
docker compose exec redis redis-cli -a change-me-redis LASTSAVE    # 1791465939
docker compose exec redis redis-cli -a change-me-redis BGSAVE      # Background saving started
docker compose exec redis redis-cli -a change-me-redis LASTSAVE    # 1791465945: the new snapshot is on disk
mkdir -p backups
docker compose cp redis:/data/dump.rdb backups/redis-dump.rdb
```

To check the backup, lose this project's keys and restore the file:

```bash
docker compose exec redis redis-cli -a change-me-redis -n 1 FLUSHDB
uv run python -m scripts.verify; echo $?                         # 997 keys differ, exit 1
docker compose stop redis                                        # Redis writes a new dump.rdb as it stops,
docker compose cp backups/redis-dump.rdb redis:/data/dump.rdb    # so copy the backup over it afterwards
docker compose start redis
uv run python -m scripts.verify; echo $?                         # OK, exit 0
```

`docker compose` finds the repository's `docker-compose.yml` from this folder too. `dump.rdb` holds every logical database, so the restore takes every project on the shared server back to the moment of the backup. With AOF on, Redis loads `appendonlydir/` at startup and ignores `dump.rdb`: back up that folder instead (`docker compose cp redis:/data/appendonlydir backups/`).

## Things to try

- Break Redis on purpose and watch the verification catch it:

  ```bash
  docker compose exec redis redis-cli -a change-me-redis -n 1 DEL customer:8:films
  uv run python -m scripts.verify; echo $?   # customer:8:films: missing 1, 10, 15, 17, 19 ... (70 in total), exit 1
  curl -i localhost:8000/verify           # 409
  ```

- Swap one member, so the size stays the same, and add a set for a customer that does not exist. A check that only compared `SCARD` would pass both:

  ```bash
  uv run python -m scripts.rebuild --mode single
  docker compose exec redis redis-cli -a change-me-redis -n 1 SREM customer:1:films 19
  docker compose exec redis redis-cli -a change-me-redis -n 1 SADD customer:1:films 99999
  docker compose exec redis redis-cli -a change-me-redis -n 1 SADD customer:9999:films 1
  uv run python -m scripts.verify; echo $?
  # customer:1:films: missing 19; extra 99999
  # customer:9999:films: no such customer in PostgreSQL (1 members)
  # 2 keys differ
  # 1
  ```

  The rebuild fixes `customer:1:films` but leaves `customer:9999:films`: it only writes the keys of customers that exist. Delete it with `DEL`, or `--flush` before the rebuild.

- Compare the two rebuilds: `uv run python -m scripts.rebuild --mode per-customer` sends about 1,000 queries and 1,000 pipelines; `--mode single` sends one query and one pipeline.
- Fire ten requests at once that all ask for the same new username, half with `"method": "watch"` and half with `"method": "lua"`:

  ```bash
  for id in $(seq 3 12); do
    method=$([ $((id % 2)) = 0 ] && echo watch || echo lua)
    curl -s -o /dev/null -w '%{http_code}\n' -X PUT localhost:8000/customers/$id/username \
         -H 'content-type: application/json' -d "{\"username\": \"same.name\", \"method\": \"$method\"}" &
  done; wait
  ```

  Exactly one gets 200; check with `SISMEMBER usernames same.name` and `HGET customer:<id> username` in `redis-cli`.
- The gap between the check and the write in `change_username_watch` is a fraction of a millisecond, so a race is hard to hit by hand. Widen it: add `time.sleep(0.2)` just before `pipe.multi()` (and `import time`), then repeat the loop above with `"method": "watch"` for every request and a new name. Still exactly one 200: the others fail with `WatchError`, retry and find the name taken. Now delete the `pipe.watch(...)` line and change `pipe.hget` and `pipe.sismember` to `r.hget` and `r.sismember` (without `WATCH`, the pipeline buffers commands until `execute()`, so they would not return an answer). Repeat with a new name: all ten get 200 and ten customers share the username.
