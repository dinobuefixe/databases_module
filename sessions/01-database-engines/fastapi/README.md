# Session 01 in FastAPI: one app, three engines

Connects to PostgreSQL, MongoDB and Redis and writes the same message to each one, as in the session 01 tutorial.

| File | What it shows |
|------|---------------|
| `app/clients.py` | One client per engine: `psycopg` for PostgreSQL, `pymongo` for MongoDB, `redis` for Redis. Creates the `hello` table. |
| `app/main.py` | `GET /health` pings each engine. `POST /hello` writes a row, a document and two keys. `GET /hello` reads them back. |

## Run it

From the root of the repository, start the engines and create this project's database:

```bash
docker compose up -d
./scripts/create-db.sh s01_fastapi
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
curl localhost:8000/health
curl -X POST localhost:8000/hello -H 'content-type: application/json' -d '{"msg": "first row"}'
curl localhost:8000/hello
```

## Things to try

- Stop one engine (`docker compose stop redis`) and call `/health` again.
- Run `docker compose down` and `docker compose up -d`, then `GET /hello`: the data is still there because it lives in Docker volumes.
- Compare what you get back from each engine: a row with fixed columns, a document with a nested list, plain string values.
