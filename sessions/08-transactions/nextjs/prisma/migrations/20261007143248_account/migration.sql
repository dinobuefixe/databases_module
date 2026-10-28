-- CreateTable
CREATE TABLE "account" (
    "id" INTEGER NOT NULL,
    "balance" DECIMAL(12,2) NOT NULL,

    CONSTRAINT "account_pkey" PRIMARY KEY ("id")
);

-- Added by hand: Prisma cannot express CHECK constraints.
ALTER TABLE "account" ADD CONSTRAINT "balance_not_negative" CHECK ("balance" >= 0);
