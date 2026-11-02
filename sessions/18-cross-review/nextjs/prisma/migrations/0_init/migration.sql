-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateTable
CREATE TABLE "customer" (
    "customer_id" SERIAL NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "email" TEXT,
    "last_update" TIMESTAMPTZ(6) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "customer_pkey" PRIMARY KEY ("customer_id")
);

-- CreateTable
CREATE TABLE "film" (
    "film_id" SERIAL NOT NULL,
    "title" TEXT NOT NULL,

    CONSTRAINT "film_pkey" PRIMARY KEY ("film_id")
);
