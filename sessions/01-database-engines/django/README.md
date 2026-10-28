# Session 01 in Django: one app, three engines

Connects to PostgreSQL, MongoDB and Redis and writes the same message to each one, as in the session 01 tutorial.

| File | What it shows |
|------|---------------|
| `demo/models.py` | The `hello` table as a Django model. Django manages PostgreSQL through its ORM and migrations. |
| `demo/clients.py` | `pymongo` and `redis` clients. Django has no built-in support for MongoDB documents or Redis data structures. |
| `demo/views.py` | `GET /health` pings each engine. `POST /hello` writes a row, a document and two keys. `GET /hello` reads them back. |
| `config/settings.py` | Reads every connection string from `.env`. Only the `demo` app is installed. |

## Run it

From the root of the repository, start the engines and create this project's database:

```bash
docker compose up -d
./scripts/create-db.sh s01_django
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

```bash
curl localhost:8001/health
curl -X POST localhost:8001/hello -H 'content-type: application/json' -d '{"msg": "first row"}'
curl localhost:8001/hello
```

## Things to try

- Stop one engine (`docker compose stop redis`) and call `/health` again.
- Run `docker compose down` and `docker compose up -d`, then `GET /hello`: the data is still there because it lives in Docker volumes.
- Open `demo/migrations/0001_initial.py` and compare it with the `CREATE TABLE` in the tutorial.
