import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { listIndexes } from "@/lib/explain";

// Create or drop the tutorial's indexes so you can compare plans.
// Usage: npm run index -- create|drop composite|partial|lower-email|single|all
//        npm run index -- list
//
// composite, partial and single are the statements Prisma generates from the
// @@index lines in prisma/schema.prisma. The expression index cannot be
// declared in Prisma.
export const INDEXES = {
  composite: {
    create: () => prisma.$executeRaw`CREATE INDEX IF NOT EXISTS big_rental_customer_rented ON big_rental (customer_id, rented_at DESC)`,
    drop: () => prisma.$executeRaw`DROP INDEX IF EXISTS big_rental_customer_rented`,
  },
  partial: {
    create: () => prisma.$executeRaw`CREATE INDEX IF NOT EXISTS big_rental_open ON big_rental (rented_at) WHERE returned_at IS NULL`,
    drop: () => prisma.$executeRaw`DROP INDEX IF EXISTS big_rental_open`,
  },
  "lower-email": {
    create: () => prisma.$executeRaw`CREATE INDEX IF NOT EXISTS customer_lower_email ON customer (lower(email))`,
    drop: () => prisma.$executeRaw`DROP INDEX IF EXISTS customer_lower_email`,
  },
  single: {
    create: () => prisma.$executeRaw`CREATE INDEX IF NOT EXISTS big_rental_rented ON big_rental (rented_at)`,
    drop: () => prisma.$executeRaw`DROP INDEX IF EXISTS big_rental_rented`,
  },
};

type IndexName = keyof typeof INDEXES;

async function main() {
  const [action, which] = process.argv.slice(2);
  if (action !== "list") {
    if ((action !== "create" && action !== "drop") || !(which === "all" || which in INDEXES)) {
      console.error("Usage: npm run index -- create|drop composite|partial|lower-email|single|all  |  npm run index -- list");
      process.exitCode = 1;
      return;
    }
    const names = which === "all" ? (Object.keys(INDEXES) as IndexName[]) : [which as IndexName];
    for (const name of names) {
      const start = performance.now();
      await INDEXES[name][action]();
      console.log(`${action} ${name}: ${Math.round(performance.now() - start)} ms`);
    }
  }
  console.table(await listIndexes());
}

if (require.main === module) main().finally(() => prisma.$disconnect());
