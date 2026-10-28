# Session 15 in FastAPI: Redis data structures and patterns

Shows each Redis structure from the tutorial behind an endpoint (counter, hash, set, sorted set), then the patterns: a weekly leaderboard, cache-aside for a customer read from PostgreSQL, a lock with safe release, and a fixed-window rate limit.

| File | What it shows |
|------|---------------|
| `app/db.py` | SQLAlchemy engine for PostgreSQL and the `redis` client on logical database `/1`. |
| `app/models.py` | `Customer` and `Film`, only the columns used. |
| `app/patterns.py` | `get_customer` / `update_customer` (cache-aside with a 300 s TTL and invalidation), `run_exclusively` (`SET NX EX` plus a Lua release script), `allow_request` (fixed window with `INCR` and `EXPIRE` in a pipeline), `record_rental` (`ZINCRBY` on this week's leaderboard and `EXPIRE ... NX`). |
| `app/main.py` | The endpoints listed below. `GET /search` is the rate-limited one. |
| `scripts/lock_demo.py` | Two threads try to run the same job at the same moment; one runs it, the other skips. |
| `scripts/leaderboard_load.py` | Sends `ZINCRBY` to this week's leaderboard in pipelined batches for a few seconds, then prints the updates per second and the top 10. |

| Endpoint | Redis commands |
|----------|----------------|
| `POST /films/{id}/views`, `GET /films/{id}/views` | `INCR film:{id}:views`, `GET` |
| `POST /films/{id}/hash`, `GET /films/{id}/hash` | `HSET film:{id} title ... rate ...`, `HGETALL` |
| `POST /visitors/{customer_id}`, `GET /visitors?day=` | `SADD visitors:{day} customer:{id}`, `SCARD` |
| `GET /search?q=`, `GET /search/popular` | `ZINCRBY search:terms 1 {q}`, `ZRANGE search:terms 0 4 REV WITHSCORES` |
| `POST /leaderboard/customers/{id}` | `ZINCRBY leaderboard:customers:{YYYY-Www} 1 customer:{id}` and `EXPIRE ... 1209600 NX` in `MULTI`/`EXEC`, then `ZREVRANK` |
| `GET /leaderboard/customers?week=`, `GET /leaderboard/customers/{id}?week=` | `ZRANGE ... 0 9 REV WITHSCORES` and `TTL`; `ZREVRANK` and `ZSCORE` |
| `GET /customers/{id}`, `PATCH /customers/{id}` | `GET` / `SET cache:customer:{id} ... EX 300`, `DEL` after the update |
| `POST /jobs/nightly-export` | `SET lock:nightly-export {token} NX EX 60`, Lua `GET` + `DEL` |

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s15_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl -X POST localhost:8000/films/42/views            # {"views": 1}, then 2, 3...
curl -X POST localhost:8000/films/1/hash              # {"title": "ACADEMY DINOSAUR", "rate": "0.99"}
curl -X POST localhost:8000/visitors/5
curl -X POST localhost:8000/visitors/9
curl -X POST localhost:8000/visitors/5                # still 2 unique visitors
curl 'localhost:8000/search?q=alien'
curl localhost:8000/search/popular

curl -X POST localhost:8000/leaderboard/customers/5    # {"rentals": 1, "rank": 1}
curl -X POST localhost:8000/leaderboard/customers/5    # {"rentals": 2, "rank": 1}
curl -X POST localhost:8000/leaderboard/customers/9    # {"rentals": 1, "rank": 2}
curl localhost:8000/leaderboard/customers              # this week's top 10 and the TTL (1209600 s, two weeks)
curl localhost:8000/leaderboard/customers/9            # {"rank": 2, "rentals": 1}

curl localhost:8000/customers/1                       # "cache": "miss"
curl localhost:8000/customers/1                       # "cache": "hit", ttl counting down
curl -X PATCH localhost:8000/customers/1 -H 'content-type: application/json' -d '{"first_name": "MARIA"}'
curl localhost:8000/customers/1                       # "miss" again, with the new name

curl -X POST 'localhost:8000/jobs/nightly-export?seconds=5' &
curl -X POST localhost:8000/jobs/nightly-export       # 409 while the first one runs
```

The lock with two workers in one process:

```bash
uv run python -m scripts.lock_demo
```

The leaderboard under load: as many `ZINCRBY` as one Python process can send in 5 seconds, in batches of 100 per round trip. Expect well over 1,000 updates per second (about 150,000 on a laptop); with `--batch 1`, one round trip per command, it drops to a few thousand. Call `GET /leaderboard/customers` while it runs to see the top 10 change.

```bash
uv run python -m scripts.leaderboard_load              # 510,200 ZINCRBY in 3.0 s: 170,058 updates per second (batch 100)
uv run python -m scripts.leaderboard_load --batch 1
```

The rate limit allows `RATE_LIMIT` requests (10 by default) per client per clock minute on `/search`, then returns 429 with a `Retry-After` header:

```bash
for i in $(seq 12); do curl -s -o /dev/null -w '%{http_code} ' 'localhost:8000/search?q=dino'; done
```

## Notes

- **One key per week.** `leaderboard:customers:2026-W41` uses the ISO week (`date.isocalendar()`), so a new week starts an empty board without deleting anything. `EXPIRE ... NX` sets the TTL only when the key has none, which is on the first write of the week; later writes do not push it back. Each week's key disappears on its own two weeks after its first write.
- **`pipeline()` and `pipeline(transaction=False)`.** In redis-py, `r.pipeline()` wraps the commands in `MULTI`/`EXEC`: they are sent in one round trip and run together, with no other client's command in between. `record_rental` and `allow_request` use it so that the `ZINCRBY` or `INCR` is never left without its `EXPIRE`. `r.pipeline(transaction=False)` only batches: one round trip, but other clients' commands can run between yours. The load script uses it, because each `ZINCRBY` is already atomic and the batch does not need to be.

## Things to try

- Open `redis-cli` on the same database and watch the keys appear:

  ```bash
  docker compose exec redis redis-cli -a change-me-redis -n 1
  ```

  then `SCAN 0 MATCH film:*`, `TTL cache:customer:1`, `ZRANGE search:terms 0 -1 REV WITHSCORES`. Use `SCAN`, not `KEYS *`.
- Change the customer directly in `psql` (`UPDATE customer SET first_name = 'X' WHERE customer_id = 1;`) and read it through the API. You get the old name until the TTL expires, because nothing deleted the key. Only writes that go through `update_customer` invalidate the cache.
- In `app/patterns.py`, replace the Lua release with a plain `r.delete(f"lock:{name}")`, and in `app/main.py` pass `ttl=1` to `run_exclusively`. Call `POST /jobs/nightly-export?seconds=3`, and two seconds later call it again: the first lock has expired, so the second call runs too. Think about whose lock the first call deletes when it finishes, and what a third call would then do.
