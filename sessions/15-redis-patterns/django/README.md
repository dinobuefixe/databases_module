# Session 15 in Django: Redis data structures and patterns

The session 15 tutorial with Django and `redis-py`: a counter, a hash, a set of daily visitors and a sorted set of search terms and a weekly leaderboard, then cache-aside for a customer with invalidation on update, a lock with safe release in Lua, and a fixed-window rate limit on one endpoint.

| File | What it shows |
|------|---------------|
| `demo/views.py` | One endpoint per structure (`INCR`, `HSET`, `SADD`/`SCARD`, `ZINCRBY`/`ZRANGE ... REV`), the leaderboard (`ZRANGE ... REV WITHSCORES`, `ZREVRANK`, `ZSCORE`), plus `GET` and `PATCH /customers/{id}`. |
| `demo/patterns.py` | The tutorial's functions: `get_customer` / `update_customer` (cache-aside), `run_exclusively` (lock with a Lua release), `allow_request` (rate limit), `record_rental` (`ZINCRBY` on this week's leaderboard and `EXPIRE ... NX`). |
| `demo/management/commands/lock_demo.py` | Starts two or more threads at the same moment; only the one that sets the lock runs the job. |
| `demo/management/commands/leaderboard_load.py` | Sends `ZINCRBY` to this week's leaderboard in pipelined batches for a few seconds, then prints the updates per second and the top 10. |
| `demo/models.py` | `film` and `customer` from Pagila, unmanaged. PostgreSQL stays the source of truth for customers. |
| `config/settings.py` | `REDIS_URL` with this project's logical database (`/2`) and `RATE_LIMIT`. |

Keys used by this project:

| Key | Type | Written by | Expiry |
|-----|------|------------|--------|
| `film:{id}:views` | string (counter) | `POST /films/{id}/views` | none |
| `film:{id}` | hash (`title`, `rate`) | `POST /films/{id}/hash` | none |
| `visitors:{YYYY-MM-DD}` | set of `customer:{id}` | `POST /visitors/{day}` | none |
| `search:terms` | sorted set, score = searches | `GET /search` | none |
| `leaderboard:customers:{YYYY-Www}` | sorted set of `customer:{id}`, score = rentals that ISO week | `POST /leaderboard/customers/{id}`, `leaderboard_load` | 14 days from the first write (`EXPIRE ... NX`) |
| `cache:customer:{id}` | string (JSON) | `GET /customers/{id}` on a miss | 300 s, deleted on `PATCH` |
| `lock:nightly-export` | string (owner token) | `lock_demo` | 60 s |
| `ratelimit:{client}:{minute}` | string (counter) | `GET /search` | 60 s |

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s15_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate            # records the unmanaged models, creates no tables
uv run python manage.py lock_demo          # 1 of 2 workers ran the job
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl -X POST localhost:8001/films/42/views
curl -X POST localhost:8001/films/42/hash
curl -X POST localhost:8001/visitors/2026-10-07 -H 'content-type: application/json' -d '{"customer_id": 5}'
curl -X POST localhost:8001/visitors/2026-10-07 -H 'content-type: application/json' -d '{"customer_id": 9}'
curl -X POST localhost:8001/visitors/2026-10-07 -H 'content-type: application/json' -d '{"customer_id": 5}'   # "added": 0, still 2 visitors
curl 'localhost:8001/search?term=alien'
curl localhost:8001/search/popular
curl -X POST localhost:8001/leaderboard/customers/5                                                       # "rentals": 1, "rank": 1
curl -X POST localhost:8001/leaderboard/customers/5                                                       # "rentals": 2
curl -X POST localhost:8001/leaderboard/customers/9                                                       # "rank": 2
curl localhost:8001/leaderboard/customers                                                                 # this week's top 10, "ttl": 1209600
curl localhost:8001/leaderboard/customers/9                                                               # "rank": 2, "rentals": 1
curl localhost:8001/customers/5                                                                          # "cache": "miss"
curl localhost:8001/customers/5                                                                          # "cache": "hit"
curl -X PATCH localhost:8001/customers/5 -H 'content-type: application/json' -d '{"email": "elizabeth.brown@example.org"}'   # "miss", new email
```

The leaderboard under load: as many `ZINCRBY` as one process can send in 5 seconds, 100 per round trip. Expect well over 1,000 updates per second (about 190,000 on a laptop); with `--batch 1`, one round trip per command, it drops to a few thousand. Call `GET /leaderboard/customers` while it runs to see the top 10 change.

```bash
uv run python manage.py leaderboard_load              # 589,700 ZINCRBY in 3.0 s: 196,544 updates per second (batch 100)
uv run python manage.py leaderboard_load --batch 1
```

`record_rental` uses `r.pipeline()`, which in redis-py wraps the commands in `MULTI`/`EXEC`: `ZINCRBY` and `EXPIRE` are sent in one round trip and run together. `leaderboard_load` uses `r.pipeline(transaction=False)`, which only batches: one round trip, but other clients' commands can run between the increments. That is enough there, because each `ZINCRBY` is atomic on its own.

Call `/search` more than `RATE_LIMIT` times within one minute to get `429` with a `Retry-After` header:

```bash
for i in $(seq 12); do curl -s -o /dev/null -w '%{http_code} ' 'localhost:8001/search?term=dinosaur'; done
```

## Things to try

- Watch the commands as they arrive: `docker compose exec redis redis-cli -a change-me-redis MONITOR` (from the repository root), then call the endpoints.
- `uv run python manage.py lock_demo --workers 10`: still only one runs the job. Then replace the Lua `release` in `patterns.py` with a plain `r.delete(...)` and think about what happens if the job takes longer than the 60-second TTL.
- Change a customer in `psql` instead of through `PATCH`. `GET /customers/{id}` keeps returning the old data until the TTL ends, because only `update_customer` deletes the key.
- Send 10 requests at the end of a minute and 10 at the start of the next one. All 20 pass: that is the weakness of a fixed window.
- List the keys with `SCAN 0 MATCH film:* COUNT 100` in `redis-cli -n 2` instead of `KEYS *`.
