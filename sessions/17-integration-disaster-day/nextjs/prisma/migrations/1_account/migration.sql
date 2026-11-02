-- Generated with:
--   prisma migrate diff --from-schema <schema without account> --to-schema prisma/schema.prisma --script
-- then edited by hand: the CHECK constraint and the two starting accounts from session 08.

-- CreateTable
CREATE TABLE "account" (
    "id" INTEGER NOT NULL,
    "balance" DECIMAL NOT NULL,

    CONSTRAINT "account_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "account_balance_check" CHECK ("balance" >= 0)
);

INSERT INTO "account" ("id", "balance") VALUES (1, 100), (2, 100);
