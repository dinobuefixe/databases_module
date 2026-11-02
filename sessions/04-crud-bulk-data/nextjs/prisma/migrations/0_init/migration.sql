-- Baseline: the Pagila tables this project maps, as they already exist in the
-- database. Never run. Marked as applied with
--   npx prisma migrate resolve --applied 0_init

-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateEnum
CREATE TYPE "mpaa_rating" AS ENUM ('G', 'PG', 'PG-13', 'R', 'NC-17');

-- CreateTable
CREATE TABLE "actor" (
    "actor_id" SERIAL NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "last_update" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "actor_pkey" PRIMARY KEY ("actor_id")
);

-- CreateTable
CREATE TABLE "film" (
    "film_id" SERIAL NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "release_year" INTEGER,
    "language_id" INTEGER NOT NULL,
    "original_language_id" INTEGER,
    "rental_duration" SMALLINT NOT NULL DEFAULT 3,
    "rental_rate" DECIMAL(4,2) NOT NULL DEFAULT 4.99,
    "length" SMALLINT,
    "replacement_cost" DECIMAL(5,2) NOT NULL DEFAULT 19.99,
    "rating" "mpaa_rating" DEFAULT 'G',
    "last_update" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "special_features" TEXT[],

    CONSTRAINT "film_pkey" PRIMARY KEY ("film_id")
);

-- CreateIndex
CREATE INDEX "idx_actor_last_name" ON "actor"("last_name");

-- CreateIndex
CREATE INDEX "idx_title" ON "film"("title");
