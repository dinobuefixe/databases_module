import "dotenv/config";
import { defineConfig } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  datasource: {
    // The Prisma CLI (db pull, migrate) works on the schema, so it connects as
    // the migrations role. The application connects as app (src/lib/prisma.ts).
    url: process.env["MIGRATIONS_DATABASE_URL"],
  },
});
