# Session 09 in Django: least privilege and injection

The session 09 tutorial on a copy of Pagila: the `migrations`, `app` and `readonly` roles with their grants and the tests that prove them, a Django app that connects as `app`, SQL injection and NoSQL injection in an unsafe and a safe version, a MongoDB user limited to one database, and a Redis ACL user that cannot run dangerous commands.

| File | What it shows |
|------|---------------|
| `config/settings.py` | Three database aliases: `default` connects as `app`, `readonly` as `readonly`, `migrations` as `migrations`. The superuser URL is not one of them. Argon2 as the password hasher. |
| `demo/management/commands/setup_roles.py` | Creates the three roles if they do not exist (passwords from `.env`) and runs the tutorial's grants on this project's database. The only code that uses `ADMIN_DATABASE_URL`. |
| `demo/management/commands/prove_permissions.py` | Logs in as each role and checks the tutorial's tests: `DROP TABLE` as `app` fails, `INSERT` as `readonly` fails, `SELECT` works, and a table created by `migrations` gets the default privileges. Everything runs in transactions that are rolled back. |
| `demo/management/commands/setup_mongo.py` | Creates the MongoDB user `app` with `readWrite` on `s09_django` only, then, connected as that user, the `users` collection (argon2 hashes) and `legacy_users` (plain text, for the unsafe demo). |
| `demo/management/commands/setup_redis.py` | `ACL SETUSER s09_django_app ... ~* +@all -@dangerous`, then shows that `SET` works and `FLUSHALL`, `FLUSHDB`, `KEYS`, `CONFIG` are refused for that user. |
| `demo/views.py` | `GET /customers/search` (ORM, parameterised) and `GET /unsafe/customers/search` (f-string). `POST /login` (type checks + `check_password`) and `POST /unsafe/login` (filter built from the body). `GET /reports/customers-per-store` reads through `readonly`. `GET /whoami` shows the user on each engine. |

The `/unsafe/...` routes are a local demonstration of what not to do. They return 404 unless `DJANGO_DEBUG=true`.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s09_django --pagila
```

Then, in this folder:

```bash
cp .env.example .env
uv sync
uv run python manage.py setup_roles
uv run python manage.py prove_permissions
uv run python manage.py setup_mongo
uv run python manage.py setup_redis
uv run python manage.py runserver 8001
```

`uv sync` creates `.venv/` with the Python version and the exact package versions in `uv.lock`. The dependencies are declared in `pyproject.toml`.

There is no `migrate` step and no `migrations` folder: the model is `managed = False` and the `app` role cannot create tables. If you add migrations, run them as the owner with `uv run python manage.py migrate --database migrations`.

The roles are shared by every database on the server. If another project already created them, `setup_roles` keeps their passwords, so the passwords in your `.env` must match.

```bash
curl localhost:8001/whoami

# SQL injection: the payload ' OR '1'='1 closes the quote and adds a condition that is always true.
curl -G localhost:8001/unsafe/customers/search --data-urlencode "email=' OR '1'='1"   # 999 rows
curl -G localhost:8001/customers/search --data-urlencode "email=' OR '1'='1"          # 0 rows
curl -G localhost:8001/customers/search --data-urlencode "email=MARY.SMITH@sakilacustomer.org"
curl localhost:8001/reports/customers-per-store

# NoSQL injection: {"$ne": null} matches any password.
curl -X POST localhost:8001/unsafe/login -d '{"username": "admin", "password": {"$ne": null}}'   # logged in
curl -X POST localhost:8001/login -d '{"username": "admin", "password": {"$ne": null}}'          # 400
curl -X POST localhost:8001/login -d '{"username": "admin", "password": "admin-demo-password"}'  # logged in
```

The demo passwords (`admin-demo-password`, `ana-demo-password`) are in `setup_mongo.py` because this is a local example.

## Things to try

- Read the `sql` field of both searches. In the unsafe one the payload is part of the SQL text; in the safe one the SQL has `%s` and the payload is in `params`.
- Try `email=' OR '1'='1'; DROP TABLE film; --` on the unsafe search. psycopg sends a query without parameters as plain text, so PostgreSQL runs both statements, and the response shows `must be owner of table film`: the app connects as `app`, which does not own `film`. Least privilege limits the damage; it does not fix the injection.
- In `uv run python manage.py shell`, compare `Customer.objects.raw("SELECT * FROM customer WHERE email = %s", [email])` with `Customer.objects.raw(f"SELECT * FROM customer WHERE email = '{email}'")`. Escape hatches such as `.raw()`, `.extra()` and `RawSQL` are only as safe as the way you pass the values.
- Start the server with `DATABASE_URL=postgresql://readonly:change-me-readonly@localhost:5432/s09_django uv run python manage.py runserver 8001` (a variable already set in the shell wins over `.env`) and call every endpoint. They all still work, because none of them writes to PostgreSQL. Which role does this app really need?
- Connect to Redis as the new user (`docker compose exec redis redis-cli --user s09_django_app --pass change-me-redis-app`) and try `SET`, `GET`, `KEYS *` and `FLUSHDB`. Do not run `FLUSHALL` as the default user: the Redis server is shared.
- In MongoDB (`docker compose exec mongo mongosh -u app -p change-me-mongo-app --authenticationDatabase s09_django s09_django`) run `show dbs` and `db.getSiblingDB("admin").system.users.findOne()`.
- `git check-ignore -v .env` shows which rule keeps `.env` out of Git.

In your own environment, the tutorial's `ALTER DATABASE pagila OWNER TO migrations` applies to your Pagila database. Here `setup_roles` refuses to run on any database whose name does not start with `s09_`, because the server is shared.
