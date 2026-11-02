-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateTable
CREATE TABLE "customer" (
    "customer_id" SERIAL NOT NULL,
    "first_name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,

    CONSTRAINT "customer_pkey" PRIMARY KEY ("customer_id")
);

-- CreateTable
CREATE TABLE "inventory" (
    "inventory_id" SERIAL NOT NULL,
    "film_id" INTEGER NOT NULL,
    "store_id" INTEGER NOT NULL,

    CONSTRAINT "inventory_pkey" PRIMARY KEY ("inventory_id")
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

-- CreateIndex
CREATE UNIQUE INDEX "idx_unq_rental_rental_date_inventory_id_customer_id" ON "rental"("rental_date", "inventory_id", "customer_id");

-- AddForeignKey
ALTER TABLE "rental" ADD CONSTRAINT "rental_customer_id_fkey" FOREIGN KEY ("customer_id") REFERENCES "customer"("customer_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "rental" ADD CONSTRAINT "rental_inventory_id_fkey" FOREIGN KEY ("inventory_id") REFERENCES "inventory"("inventory_id") ON DELETE RESTRICT ON UPDATE CASCADE;
