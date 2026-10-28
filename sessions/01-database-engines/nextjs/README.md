# Session 01 in Next.js with Prisma: one app, three engines

Connects to PostgreSQL, MongoDB and Redis and writes the same message to each one, as in the session 01 tutorial.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | The `hello` table as a Prisma model. |
| `src/lib/prisma.ts` | Prisma 7 client with the PostgreSQL driver adapter. |
| `src/lib/mongo.ts` | The official `mongodb` driver. Prisma 7 does not support MongoDB. |
| `src/lib/redis.ts` | The official `redis` client, connected once and shared. |
| `src/app/api/health/route.ts` | `GET /api/health` pings each engine. |
| `src/app/api/hello/route.ts` | `POST /api/hello` writes a row, a document and two keys. `GET /api/hello` reads them back. |

## Run it

From the root of the repository, start the engines and create this project's database:

```bash
docker compose up -d
./scripts/create-db.sh s01_nextjs
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npx prisma migrate dev
npm run dev
```

`npm install` also runs `prisma generate`, which writes the typed client to `src/generated/prisma`.

```bash
curl localhost:3000/api/health
curl -X POST localhost:3000/api/hello -H 'content-type: application/json' -d '{"msg": "first row"}'
curl localhost:3000/api/hello
```

## Things to try

- Stop one engine (`docker compose stop redis`) and call `/api/health` again.
- Run `docker compose down` and `docker compose up -d`, then `GET /api/hello`: the data is still there because it lives in Docker volumes.
- Open `prisma/migrations/*/migration.sql` and compare it with the `CREATE TABLE` in the tutorial.
