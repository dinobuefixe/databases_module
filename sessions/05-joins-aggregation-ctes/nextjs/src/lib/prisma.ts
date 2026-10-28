import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });

// Log every SQL statement so you can compare what the ORM sends with the
// hand-written SQL. Set LOG_QUERIES=0 to turn it off.
function createClient() {
  const client = new PrismaClient({ adapter, log: [{ emit: "event", level: "query" }] });
  client.$on("query", (e) => {
    if (process.env.LOG_QUERIES !== "0") console.log(`[sql ${e.duration} ms] ${e.query}\n  params: ${e.params}`);
  });
  return client;
}

// Reuse one client across hot reloads in development.
const globalForPrisma = globalThis as unknown as { prisma?: ReturnType<typeof createClient> };

export const prisma = globalForPrisma.prisma ?? createClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
