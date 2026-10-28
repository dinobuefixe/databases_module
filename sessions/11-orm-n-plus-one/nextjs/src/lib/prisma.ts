import { AsyncLocalStorage } from "node:async_hooks";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/generated/prisma/client";

// Each request (or script block) gets its own list of SQL statements.
const statements = new AsyncLocalStorage<string[]>();

function createClient() {
  const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
  // emit: "event" makes Prisma call $on("query") for every SQL statement it sends.
  const client = new PrismaClient({ adapter, log: [{ emit: "event", level: "query" }] });
  client.$on("query", (e) => {
    statements.getStore()?.push(e.query);
    if (process.env.LOG_SQL === "true") {
      console.log(`[sql ${e.duration.toFixed(1)} ms] ${e.query} ${e.params}`);
    }
  });
  return client;
}

// Reuse one client across hot reloads in development.
const globalForPrisma = globalThis as unknown as { prisma?: ReturnType<typeof createClient> };

export const prisma = globalForPrisma.prisma ?? createClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

// Runs fn and returns its result with the SQL statements it caused.
export async function countQueries<T>(fn: () => Promise<T>): Promise<{ result: T; sql: string[] }> {
  const sql: string[] = [];
  const result = await statements.run(sql, fn);
  return { result, sql };
}
