-- Reverts add_customer_tier. Prisma Migrate has no down migrations; run with `npm run db:down`.
ALTER TABLE "customer" DROP COLUMN "tier";
