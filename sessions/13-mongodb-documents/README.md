# Session 13: MongoDB documents, CRUD and validation

The tutorial from [session 13](../../README.md#session-13-mongodb-i-documents-crud-and-validation), written three times as independent projects.

Pagila's stores copied from PostgreSQL into a `stores` collection with the manager, address and staff embedded, then queried with dot notation, updated with `$push` and `$inc`, protected by a `$jsonSchema` validator and indexed, with `explain` before and after.

| Project | Approach | Port |
|---------|----------|------|
| [fastapi](fastapi/) | `pymongo` | 8000 |
| [django](django/) | `pymongo` (Django ORM for the PostgreSQL side) | 8001 |
| [nextjs](nextjs/) | `mongodb` driver (Prisma only for PostgreSQL) | 3000 |

Prisma 7 does not support MongoDB, so the Next.js project uses the official driver, which reads almost the same as `mongosh` and `pymongo`.
