-- Baseline: the Pagila tables this project maps, as they already exist in the
-- database. Never run. Marked as applied with
--   npx prisma migrate resolve --applied 0_init

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateEnum
CREATE TYPE "mpaa_rating" AS ENUM ('G', 'PG', 'PG-13', 'R', 'NC-17');

-- CreateTable
CREATE TABLE "film" (
    "film_id" SERIAL NOT NULL,
    "title" TEXT NOT NULL,
    "length" SMALLINT,
    "rating" "mpaa_rating" DEFAULT 'G',

    CONSTRAINT "film_pkey" PRIMARY KEY ("film_id")
);

-- CreateTable
CREATE TABLE "rental" (
    "rental_id" SERIAL NOT NULL,
    "rental_date" TIMESTAMPTZ(6) NOT NULL,
    "inventory_id" INTEGER NOT NULL,
    "customer_id" INTEGER NOT NULL,
    "return_date" TIMESTAMPTZ(6),
    "staff_id" INTEGER NOT NULL,

    CONSTRAINT "rental_pkey" PRIMARY KEY ("rental_id")
);

-- CreateTable
CREATE TABLE "payment" (
    "payment_id" SERIAL NOT NULL,
    "customer_id" INTEGER NOT NULL,
    "staff_id" INTEGER NOT NULL,
    "rental_id" INTEGER NOT NULL,
    "amount" DECIMAL(5,2) NOT NULL,
    "payment_date" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "payment_pkey" PRIMARY KEY ("payment_date","payment_id")
);

