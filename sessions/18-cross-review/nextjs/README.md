# Film ratings

Customers rate Pagila films from 1 to 5 stars. The API also searches customers and serves their profiles.

## Stack

- Next.js 16 (route handlers) and TypeScript
- PostgreSQL with Prisma 7
- Redis for profiles and rating summaries

## How to run

```bash
# from the root of the repository
docker compose up -d
./scripts/create-db.sh s18_nextjs --pagila

# in this folder
cp .env.example .env
npm install
npx prisma migrate resolve --applied 0_init
npm run db:deploy
npm run dev
```

```bash
curl 'localhost:3000/api/customers/search?q=smi'
curl 'localhost:3000/api/customers/by-email?email=mary.smith@sakilacustomer.org'
curl localhost:3000/api/customers/1/profile
curl -X PUT localhost:3000/api/admin/customers/1/profile -H 'content-type: application/json' -d '{"first_name": "MARY", "last_name": "SMITH"}'
curl -X POST localhost:3000/api/films/1/ratings -H 'content-type: application/json' -d '{"customer_id": 1, "stars": 4}'
curl localhost:3000/api/films/1/rating
```
