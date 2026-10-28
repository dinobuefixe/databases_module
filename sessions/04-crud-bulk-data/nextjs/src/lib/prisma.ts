import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/generated/prisma/client";

// Reuse one client across hot reloads in development.
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });

// LOG_QUERIES=1 prints every SQL statement Prisma sends.
export const prisma =
  globalForPrisma.prisma ?? new PrismaClient({ adapter, log: process.env.LOG_QUERIES ? ["query"] : [] });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
