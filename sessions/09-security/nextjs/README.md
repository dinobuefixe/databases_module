# Session 09 in Next.js with Prisma: security

Least privilege on all three engines and the two injection attacks from the tutorial. PostgreSQL gets the `migrations`, `app` and `readonly` roles, MongoDB an application user limited to one database, and Redis an ACL user that cannot run dangerous commands. The application connects as those users, never as the superuser. Two endpoints are vulnerable on purpose, next to their safe versions.

**The endpoints marked UNSAFE are for a local demonstration only.** Do not copy them.

| File | What it shows |
|------|---------------|
| `scripts/setup-postgres.ts` | Creates the three roles if missing (password from `.env`), makes `migrations` the database owner, and runs the tutorial's `GRANT`, `REVOKE` and `ALTER DEFAULT PRIVILEGES`. Runs as the superuser. |
| `scripts/prove-postgres.ts` | The permission tests, connected as `app` and as `readonly`: `DROP TABLE` as `app` fails, `INSERT` as `readonly` fails. |
| `scripts/setup-mongo.ts` | Creates the MongoDB user `app` with `readWrite` on `s09_nextjs` only, loads the login demo users, and shows `app` cannot read another database. |
| `scripts/setup-redis.ts` | Creates the Redis ACL user `s09_nextjs_app` (`+@all -@dangerous`) and shows `FLUSHALL` is refused. |
| `prisma.config.ts` | The Prisma CLI uses `MIGRATIONS_DATABASE_URL`; the app uses `DATABASE_URL` (`app`). |
| `src/app/api/whoami/route.ts` | `GET /api/whoami`: the user the app is connected as on each engine. |
| `src/app/api/customers/search/route.ts` | Safe search: `$queryRaw` tagged template, the email travels as a parameter. |
| `src/app/api/customers/search-unsafe/route.ts` | **UNSAFE** search: the email is pasted into the SQL and run with `$queryRawUnsafe`. |
| `src/app/api/login/route.ts` | Safe login: type checks, lookup by username, bcrypt hash comparison. |
| `src/app/api/login-unsafe/route.ts` | **UNSAFE** login: plain-text passwords and a filter built from the request body. |

## Secrets

Every password is in `.env`, which the repository's `.gitignore` excludes. `.env.example` holds the variable names and placeholder values and is committed. There are four kinds of connection:

| Variable | User | Used by |
|----------|------|---------|
| `ADMIN_DATABASE_URL`, `MONGO_ADMIN_URL`, `REDIS_ADMIN_URL` | superuser / root / default | the setup scripts only |
| `MIGRATIONS_DATABASE_URL` | `migrations` | the Prisma CLI |
| `DATABASE_URL`, `MONGO_URL`, `REDIS_URL` | `app`, `app`, `s09_nextjs_app` | the application |
| `READONLY_DATABASE_URL` | `readonly` | reports (here, the permission tests) |

The PostgreSQL roles belong to the whole server, and other projects in this repository share them. The setup script never drops a role and never changes the password of an existing one. In Redis the user is called `s09_nextjs_app`, not `app`, for the same reason.

## Run it

From the root of the repository:

```bash
docker compose up -d
./scripts/create-db.sh s09_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run setup:postgres
npm run prove:postgres
npm run setup:mongo
npm run setup:redis
npm run dev
```

`npm run prove:postgres`:

```
PASS  app      SELECT from customer   allowed
PASS  app      INSERT into actor      allowed
PASS  app      DROP TABLE film        refused: must be owner of table film
PASS  app      CREATE TABLE           refused: permission denied for schema public
PASS  readonly SELECT from actor      allowed
PASS  readonly INSERT into actor      refused: permission denied for table actor
```

Each test runs inside `BEGIN ... ROLLBACK`, so nothing changes even when a statement is allowed.

`npm run setup:redis` ends with:

```
PASS  FLUSHALL refused: NOPERM User s09_nextjs_app has no permissions to run the 'flushall' command
```

The script first asks Redis with `ACL DRYRUN` whether the user may run `FLUSHALL`, and only sends the command when the answer is no. Never run `FLUSHALL` as the default user on a shared server.

### SQL injection

```bash
curl localhost:3000/api/whoami
curl -G localhost:3000/api/customers/search --data-urlencode "email=MARY.SMITH@sakilacustomer.org"   # 1 row
curl -G localhost:3000/api/customers/search-unsafe --data-urlencode "email=' OR '1'='1"             # 999 rows
curl -G localhost:3000/api/customers/search --data-urlencode "email=' OR '1'='1"                    # 0 rows
```

The unsafe endpoint returns the SQL it ran: `... WHERE email = '' OR '1'='1'`. The input closed the string and added a condition that is always true. The safe endpoint sends the same input as a value and finds no customer with that email.

Now try to destroy something through the unsafe endpoint:

```bash
curl -G localhost:3000/api/customers/search-unsafe --data-urlencode "email='; DROP TABLE film; --"
```

The injection works (the error comes from the `DROP TABLE`, so PostgreSQL received and ran it), but the statement fails with `must be owner of table film`: the app connects as `app`, which cannot drop tables. Least privilege did not stop the injection; it limited the damage. Connected as `postgres`, the table would be gone.

### NoSQL injection

```bash
curl -X POST localhost:3000/api/login-unsafe -H 'content-type: application/json' \
  -d '{"username": "admin", "password": "wrong"}'               # 401
curl -X POST localhost:3000/api/login-unsafe -H 'content-type: application/json' \
  -d '{"username": "admin", "password": {"$ne": null}}'         # 200, logged in as admin
curl -X POST localhost:3000/api/login -H 'content-type: application/json' \
  -d '{"username": "admin", "password": {"$ne": null}}'         # 400, password must be a string
curl -X POST localhost:3000/api/login -H 'content-type: application/json' \
  -d '{"username": "admin", "password": "correct horse battery staple"}'   # 200
```

The unsafe endpoint passes `body.password` into the filter. `{"$ne": null}` is an operator, so the filter means "admin, with any password". The safe endpoint refuses anything that is not a string, finds the user by username, and checks the password against a bcrypt hash with `bcrypt.compare`. The `users` collection stores only hashes; `legacy_users` stores plain text only to show what not to do.

## Things to try

- In `psql` as the superuser (`docker compose exec postgres psql -U postgres -d s09_nextjs`), run the tutorial's tests with `SET ROLE app; DROP TABLE film;` and `SET ROLE readonly; INSERT INTO actor ...`, then `RESET ROLE`.
- Change `DATABASE_URL` in `.env` to the `postgres` superuser, restart, and look at `/api/whoami`. Do not run the `DROP TABLE` payload after that.
- Run `npx prisma db pull --print`: it connects as `migrations` and works. Set `MIGRATIONS_DATABASE_URL` to the `readonly` URL and try `npx prisma migrate dev`.
- `docker compose exec redis redis-cli --user s09_nextjs_app --pass change-me-redis-app` and try `KEYS *`, `CONFIG GET maxmemory` and `FLUSHDB`. All three are in `@dangerous`.
- Look at a stored hash in MongoDB (`db.users.findOne()` in `mongosh`). Hash the same password twice with `bcrypt.hash` and compare: the salt makes every hash different.
