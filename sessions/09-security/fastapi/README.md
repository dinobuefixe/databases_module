# Session 09 in FastAPI: security

The session 09 tutorial on a copy of Pagila: least-privilege roles in PostgreSQL, SQL injection and its fix, NoSQL injection and its fix, a MongoDB user limited to one database, a Redis ACL user that cannot run dangerous commands, secrets in `.env` and passwords stored as argon2 hashes.

| File | What it shows |
|------|---------------|
| `.env.example` | Every secret the project needs, with placeholder values. The superuser, Mongo root and Redis default URLs are only read by the setup scripts. |
| `scripts/setup_postgres.py` | Creates `migrations`, `app` and `readonly` if they do not exist, and runs the tutorial's `GRANT`, `REVOKE` and `ALTER DEFAULT PRIVILEGES` on this project's database. It also grants `CREATE` on `public` to `migrations`, because Pagila's schema belongs to `postgres`. Safe to run again. |
| `scripts/prove_permissions.py` | Connects as `app` and as `readonly` and shows what each may do: `DROP TABLE film` as `app` fails, `INSERT` as `readonly` fails. Rolls back every change. |
| `scripts/setup_mongo.py` | Creates the MongoDB user `app` with `readWrite` on `s09_fastapi` only, seeds `users` with argon2 hashes, and shows a write to another database being refused. |
| `scripts/setup_redis.py` | Creates the ACL user `s09_fastapi_app` with `~* +@all -@dangerous`, then shows `SET` working and `FLUSHALL`, `FLUSHDB`, `KEYS` and `CONFIG` refused. |
| `app/clients.py` | The application's connections: `app` and `readonly` in PostgreSQL, the limited users in MongoDB and Redis. |
| `app/main.py` | `GET /whoami`, `GET /customers/search-unsafe` and `GET /customers/search`, `GET /reports/customers-per-store` (as `readonly`), `POST /login-unsafe` and `POST /login`. |

**The `-unsafe` endpoints are deliberately vulnerable.** They exist to be attacked on your own machine. Never copy them into a real project.

## Run it

From the root of the repository, start the engines and create this project's database as a copy of Pagila:

```bash
docker compose up -d
./scripts/create-db.sh s09_fastapi --pagila
```

Then, in this folder:

```bash
cp .env.example .env               # then change every password
uv sync
uv run python -m scripts.setup_postgres
uv run python -m scripts.prove_permissions
uv run python -m scripts.setup_mongo
uv run python -m scripts.setup_redis
uv run uvicorn app.main:app --reload --port 8000
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

`setup_postgres` never changes the password of a role that already exists, because roles are shared by every database on the server. If you created `app` earlier with another password, set it once as the superuser with `ALTER ROLE app PASSWORD '...'` (or `\password app` in `psql`).

Open http://127.0.0.1:8000/docs, or use `curl`:

```bash
curl localhost:8000/whoami
```

SQL injection. The payload `' OR '1'='1` closes the string and adds a condition that is always true:

```bash
curl -G localhost:8000/customers/search-unsafe --data-urlencode "email=' OR '1'='1"   # 999 rows
curl -G localhost:8000/customers/search --data-urlencode "email=' OR '1'='1"          # 0 rows
curl -G localhost:8000/customers/search --data-urlencode "email=MARY.SMITH@sakilacustomer.org"
```

The response includes the SQL that ran. In the unsafe one the input has become part of the code: `WHERE email = '' OR '1'='1'`.

Least privilege limits the damage. Try a payload that drops a table:

```bash
curl -G localhost:8000/customers/search-unsafe --data-urlencode "email='; DROP TABLE film; --"
```

The response is a 500 and the server log shows `must be owner of table film`. The injection worked, but the `app` role cannot drop tables. Had the application connected as `postgres`, `film` would be gone.

NoSQL injection:

```bash
curl -X POST localhost:8000/login-unsafe -H 'content-type: application/json' \
  -d '{"username": "admin", "password": {"$ne": null}}'          # 200, logged in as admin
curl -X POST localhost:8000/login -H 'content-type: application/json' \
  -d '{"username": "admin", "password": {"$ne": null}}'          # 422, password must be a string
curl -X POST localhost:8000/login -H 'content-type: application/json' \
  -d '{"username": "admin", "password": "admin-demo-password"}'  # 200
```

The unsafe login puts the request body straight into the MongoDB filter, so `{"$ne": null}` becomes "password is not null". To make that comparison possible it reads `legacy_users`, which stores plain-text passwords the way old code often did: a second mistake, kept only for the demo. The safe login validates types with Pydantic, looks the user up by username only, and checks the argon2 hash in Python.

## Things to try

- Repeat the tutorial's role test in `psql` as the superuser: `docker compose exec postgres psql -U postgres -d s09_fastapi`, then `SET ROLE app; DROP TABLE film;`, `RESET ROLE; SET ROLE readonly; INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y');`.
- Check the default privileges: `\ddp` in `psql`. Then `SET ROLE migrations; CREATE TABLE note (id int); RESET ROLE; SET ROLE readonly; SELECT * FROM note;` works without a new `GRANT`. Drop the table as `migrations` afterwards.
- Change `DATABASE_URL` in `.env` to the `postgres` superuser and run `prove_permissions` again. No test is refused for lack of privilege any more; `DROP TABLE film` now fails only because views and foreign keys depend on it. Change it back.
- In `mongosh`, log in as the application user and try another database: `docker compose exec mongo mongosh -u app -p change-me-mongo-app --authenticationDatabase s09_fastapi`, then `use other_db` and `db.x.insertOne({})`.
- As the Redis user, try `redis-cli --user s09_fastapi_app --pass change-me-redis-app -n 1` (inside the container: `docker compose exec redis redis-cli ...`) and run `SET a 1`, `KEYS *`, `FLUSHALL`. Never run `FLUSHALL` as the default user on this shared setup.
- `git check-ignore -v .env` shows which `.gitignore` rule keeps your secrets out of Git.
- Look at a stored hash: `db.users.findOne({username: "maria"})`. The `$argon2id$` prefix records the algorithm and its parameters, and the salt is different for every user even with the same password.
