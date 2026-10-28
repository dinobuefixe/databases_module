# Session 13 in Next.js with Prisma: MongoDB documents, CRUD and validation

Builds a `stores` collection from Pagila with the manager, address and staff embedded, then runs the session 13 tutorial against it: `find` with dot notation and a projection, `$push`, `$inc`, a `$jsonSchema` validator and an index checked with `explain("executionStats")`.

| File | What it shows |
|------|---------------|
| `prisma/schema.prisma` | The five Pagila tables a store document is built from, trimmed from `npx prisma db pull`. |
| `scripts/sync-stores.ts` | `npm run sync`: reads stores with nested `include`s (address, city, country, staff) and upserts one document per store with `bulkWrite`. |
| `scripts/apply-validator.ts` | `npm run validator`: `collMod` with the tutorial's `$jsonSchema`, `validationLevel` and `validationAction`, then the invalid insert and the error details. |
| `scripts/explain-index.ts` | `npm run explain`: `executionStats` before and after `createIndex({"address.country": 1})`. |
| `src/lib/stores.ts` | The document shape, the validator and the explain summary. |
| `src/lib/mongo.ts` | The official `mongodb` driver. Prisma 7 does not support MongoDB. |
| `src/app/api/stores/route.ts` | `GET` by country with a projection; `POST` inserts the body as it is and returns 422 with the validator's reasons. |
| `src/app/api/stores/[id]/staff/route.ts` | `$push` a staff member into the embedded array. |
| `src/app/api/stores/[id]/visits/route.ts` | `$inc` a counter that does not exist yet. |
| `src/app/api/stores/explain/route.ts` | The current plan for the find by country. |

The tutorial uses a database called `pagila_docs`. Here the MongoDB database is `s13_nextjs` (`MONGO_DB` in `.env`). This copy of Pagila has 500 stores, so the difference the index makes is easier to see than with the classic 2.

## Run it

From the root of the repository, start the engines and create this project's PostgreSQL database as a copy of Pagila. The MongoDB database is created on the first write.

```bash
docker compose up -d
./scripts/create-db.sh s13_nextjs --pagila
```

Then, in this folder:

```bash
cp .env.example .env
npm install
npm run sync        # Read 500 stores: 500 inserted
npm run validator   # Rejected: Document failed validation, with the reasons
npm run explain     # COLLSCAN, 500 examined -> IXSCAN, 54 examined
npm run dev
```

```bash
curl 'localhost:3000/api/stores?country=Canada'
curl localhost:3000/api/stores/1
curl -X POST localhost:3000/api/stores/1/staff -H 'content-type: application/json' -d '{"staff_id": 3, "name": "New Hire"}'
curl -X POST localhost:3000/api/stores/1/visits
curl -X POST localhost:3000/api/stores -H 'content-type: application/json' -d '{"_id": 9999, "address": {"city": 42}}'   # 422
curl -X POST localhost:3000/api/stores -H 'content-type: application/json' \
    -d '{"_id": 9999, "manager": {"staff_id": 1, "name": "Mike Hillyer"}, "address": {"line": "47 MySakila Drive", "city": "Lethbridge", "country": "Canada"}, "staff": []}'  # 201
curl 'localhost:3000/api/stores/explain?country=Canada'
```

The same commands in `mongosh`:

```bash
docker compose exec mongo mongosh "mongodb://root:change-me-mongo@localhost:27017/s13_nextjs?authSource=admin"
```

## Things to try

- Call `/visits` on a store, then run `npm run sync` again. `visits` survives because the sync only `$set`s the fields it owns, but the staff member you pushed is gone: PostgreSQL is the source of truth for staff, and the document is rebuilt from it.
- Run `npm run explain Canada` and compare `totalDocsExamined` with `nReturned` before and after. Then drop the index in `mongosh` (`db.stores.dropIndex("address.country_1")`) and call `/api/stores/explain` again.
- Change `validationAction` to `"warn"` in `scripts/apply-validator.ts`, run it, and post the invalid document again. It is accepted, and the warning appears in `docker compose logs mongo`.
- Before running `npm run validator`, insert an invalid document. With `validationLevel: "strict"` an update to it is rejected; with `"moderate"` it is allowed. Try both with `$inc` on `visits`.
- In `src/app/api/stores/[id]/staff/route.ts`, replace `$push` with `$addToSet` and post the same staff member twice.
