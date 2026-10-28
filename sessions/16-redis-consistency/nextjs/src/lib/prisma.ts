import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/generated/prisma/client";

const client = (url: string | undefined) => new PrismaClient({ adapter: new PrismaPg({ connectionString: url }) });

// Reuse the clients across hot reloads in development.
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient; prismaReadonly?: PrismaClient };

export const prisma = globalForPrisma.prisma ?? client(process.env.DATABASE_URL);

// Reports only read PostgreSQL, so they can use a role that cannot write.
export const prismaReadonly =
  globalForPrisma.prismaReadonly ?? client(process.env.READONLY_DATABASE_URL || process.env.DATABASE_URL);

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
  globalForPrisma.prismaReadonly = prismaReadonly;
}
