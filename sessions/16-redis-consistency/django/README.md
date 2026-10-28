# Session 16 in Django: source of truth, rebuild and verification

The session 16 tutorial with Django and `redis-py`: the `customer:{id}:films` sets derived from PostgreSQL, rebuilt into a temporary key and renamed, first with one query per customer and then with one query and one pipeline; a verification command that exits non-zero on a mismatch; the server's persistence settings, a demo that kills Redis mid-write with RDB and with AOF, and a backup and restore of Redis; and a username change with `WATCH` and with a Lua script.

| File | What it shows |
|------|---------------|
| `demo/derived.py` | `rebuild_customer` (the tutorial's version), `rebuild_single_query` (one query, one pipeline) and `verify` (every set compared member by member with PostgreSQL, plus a `SCAN` for sets of customers that do not exist). |
| `demo/management/commands/rebuild_films.py` | Runs both rebuilds, or one with `--mode`, and prints the time each takes. |
| `demo/management/commands/verify_films.py` | Exit code 0 when every set matches PostgreSQL, 1 with the differences on stderr otherwise. |
| `demo/management/commands/persistence_demo.py` | Writes in a loop, kills Redis with `docker compose kill redis`, starts it again and reports how many writes survived. |
| `demo/management/commands/flushdb.py` | `FLUSHDB` on this project's Redis database, to test the rebuild from empty. |
| `demo/views.py` | `GET /customers/{id}/films`, `GET /verify` (200 or 409), `GET /redis/persistence` (`CONFIG GET`), `PUT /customers/{id}/username?impl=watch\|lua` (both read the old name inside the transaction). |
| `config/settings.py` | A `readonly` database alias: rebuild and verify only read PostgreSQL. |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s16_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate            # records the unmanaged models, creates no tables
uv run python manage.py flushdb
uv run python manage.py verify_films; echo "exit code $?"     # 997 keys differ, exit code 1
uv run python manage.py rebuild_films                         # per-customer about 1.4 s, single-query about 0.5 s
uv run python manage.py verify_films; echo "exit code $?"     # all match, exit code 0
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl localhost:8001/customers/1/films
curl localhost:8001/verify
curl localhost:8001/redis/persistence
curl -X PUT 'localhost:8001/customers/5/username?impl=watch' -H 'content-type: application/json' -d '{"username": "eliza"}'
curl -X PUT 'localhost:8001/customers/9/username?impl=lua' -H 'content-type: application/json' -d '{"username": "eliza"}'    # 409, taken
curl -X PUT 'localhost:8001/customers/9/username?impl=lua' -H 'content-type: application/json' -d '{"username": "maggie"}'
```

## FLUSHDB instead of FLUSHALL

The tutorial tests the rebuild after `FLUSHALL`, which empties every logical database on the Redis server. In this repository one Redis server is shared by the FastAPI, Django and Next.js projects (`/1`, `/2`, `/3`), so this project uses `FLUSHDB`, which empties only `/2`. In your group project, with a Redis server of your own, `docker compose exec redis redis-cli -a <password> FLUSHALL` is the real test.

## Recommended persistence settings

`GET /redis/persistence` shows what the server runs with now. The repository's `docker-compose.yml` uses the defaults: RDB snapshots (`save 3600 1 300 100 60 10000`: after 3600 s if 1 key changed, 300 s if 100 changed, 60 s if 10,000 changed), no AOF, no memory limit. For a Redis that holds data you cannot rebuild, the tutorial's settings go in `redis.conf` or as `command` arguments:

```yaml
command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}",
          "--appendonly", "yes", "--appendfsync", "everysec",
          "--maxmemory", "256mb", "--maxmemory-policy", "noeviction"]
```

- `appendonly yes` with `appendfsync everysec`: at most about one second of writes lost in a crash.
- `noeviction`: when memory is full Redis refuses writes instead of silently deleting keys.
- If everything in Redis is derived (like `customer:{id}:films`) or ephemeral, `allkeys-lru` and no persistence are reasonable: the rebuild restores it.

This project never calls `CONFIG SET`: the server is shared, and a setting changed at runtime is lost on restart anyway. The one exception is the first step of turning AOF on, below.

## Kill Redis mid-write: RDB, then AOF

`persistence_demo` INCRs a counter as fast as it can, runs `docker compose kill redis` after two seconds, starts Redis again and compares the last value Redis acknowledged with the value it loaded from disk. `kill` sends SIGKILL: Redis cannot save anything on the way out, as in a crash.

The Redis container is shared by every project in this repository. The kill stops it for all of them for about a second, and with RDB they also lose their writes since the last snapshot. Run it when nothing else depends on Redis.

With the default server:

```bash
uv run python manage.py persistence_demo
```

```
Persistence: RDB snapshots only (appendonly no)
Writes acknowledged before the kill: 12635
Writes started at 13:28:06; last RDB snapshot before the kill: 13:27:30
Redis answers again after 0.2 s
Counter after the restart: 0
Lost: 12635 writes (100%)
```

Redis came back with the last snapshot, so every write after it is gone, including the film sets written since then:

```bash
uv run python manage.py verify_films; echo "exit code $?"     # 838 keys differ (999 customers checked), exit code 1
uv run python manage.py rebuild_films --mode single-query
uv run python manage.py verify_films; echo "exit code $?"     # All 999 customers match, exit code 0
```

Turn AOF on. From the root of the repository:

```bash
docker compose exec redis redis-cli -a change-me-redis CONFIG SET appendonly yes
docker compose -f docker-compose.yml -f docker-compose.redis-aof.yml up -d --wait redis
```

The `CONFIG SET` makes the running server write its current keys to a new AOF. The second command recreates the container with `--appendonly yes --appendfsync everysec` (from `docker-compose.redis-aof.yml`), so the setting survives restarts; Redis is unreachable for about six seconds. Without the first step, Redis starts with `appendonly yes`, finds no AOF, starts empty and ignores `dump.rdb`: every project would lose its keys.

The same demo, three runs:

```
Persistence: AOF, appendfsync everysec
Writes acknowledged before the kill: 9136
Counter after the restart: 9136
Lost: 0 writes (0%)
Writes acknowledged before the kill: 11678
Counter after the restart: 11678
Lost: 0 writes (0%)
Writes acknowledged before the kill: 11266
Counter after the restart: 11266
Lost: 0 writes (0%)
```

and `verify_films` passes without a rebuild. Not even the last second is lost: Redis passes each write to the operating system before it replies, and SIGKILL stops the process, not the machine, so the data still reaches the file. `everysec` is how often Redis forces the file onto the disk with `fsync`; the second you can lose is for a power cut or a kernel crash, which `docker compose kill` cannot simulate.

Back to the default, which the other sessions expect (from the root):

```bash
docker compose up -d --wait redis
```

Redis saves a snapshot as it stops and the new container loads it, so no keys are lost. The `appendonlydir/` folder stays in the volume, unused; the `CONFIG SET` step replaces it the next time.

## Back up and restore Redis

With the default server the backup is `dump.rdb`. `BGSAVE` writes a snapshot in the background and `LASTSAVE` (seconds since 1970) changes when it is on disk. `backups/` is in `.gitignore`.

```bash
docker compose exec redis redis-cli -a change-me-redis LASTSAVE    # 1791466469
docker compose exec redis redis-cli -a change-me-redis BGSAVE      # Background saving started
docker compose exec redis redis-cli -a change-me-redis LASTSAVE    # 1791466475: done
mkdir -p backups
docker compose cp redis:/data/dump.rdb backups/redis-dump.rdb
```

Check that the backup restores:

```bash
uv run python manage.py flushdb
uv run python manage.py verify_films; echo "exit code $?"     # 997 keys differ, exit code 1
docker compose stop redis                                     # Redis writes a new dump.rdb as it stops,
docker compose cp backups/redis-dump.rdb redis:/data/dump.rdb # so copy the backup over it afterwards
docker compose start redis
uv run python manage.py verify_films; echo "exit code $?"     # All 999 customers match, exit code 0
```

`docker compose` finds the repository's `docker-compose.yml` from this folder too. `dump.rdb` holds every logical database, so a restore takes every project on the shared server back to the moment of the backup. With AOF on, Redis loads `appendonlydir/` and ignores `dump.rdb`: back up that folder instead (`docker compose cp redis:/data/appendonlydir backups/`).

## Things to try

- Swap one film in a set for another (`SREM customer:1:films 3`, then `SADD customer:1:films 99999` in `redis-cli -n 2`), so its size does not change, and run `verify_films` (`customer:1:films: missing 3; extra 99999`) and `GET /verify` (409) again. Then `SADD customer:9999:films 1`: there is no customer 9999, and `verify_films` reports `customer:9999:films: no such customer in PostgreSQL (1 members)`. `rebuild_films` does not remove that key, because it only writes the keys of customers that exist; `flushdb` before the rebuild does.
- Set the usernames, run `flushdb` and `rebuild_films`, then `verify_films`: it passes, but the usernames are gone. Nothing rebuilds them because Redis is their only copy here. Where should a username live?
- Fire 20 username changes to the same name at once. Only one gets `200`; the others get `409`. Run it again with `impl=lua` and a different name to compare:

  ```bash
  seq 100 119 | xargs -P 20 -I{} curl -s -o /dev/null -w '%{http_code}\n' -X PUT \
      'localhost:8001/customers/{}/username?impl=watch' -H 'content-type: application/json' -d '{"username": "popular"}' | sort | uniq -c
  ```

- Put a breakpoint (or `time.sleep(5)`) between `pipe.watch` and `pipe.multi()` in `change_username_watch`, change `usernames` from `redis-cli` meanwhile, and watch the retry.
- Run `redis-cli -a change-me-redis MONITOR` while each rebuild runs. The per-customer version sends one `MULTI`/`EXEC` per customer after one PostgreSQL query per customer; the single-query version sends everything in one batch after one query.
