-- CreateTable
CREATE TABLE "film_rating" (
    "customer_id" INTEGER NOT NULL,
    "film_id" INTEGER NOT NULL,
    "stars" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "film_rating_pkey" PRIMARY KEY ("customer_id","film_id")
);

-- CreateIndex
CREATE INDEX "film_rating_created_at_idx" ON "film_rating"("created_at");

-- AddForeignKey
ALTER TABLE "film_rating" ADD CONSTRAINT "film_rating_customer_id_fkey" FOREIGN KEY ("customer_id") REFERENCES "customer"("customer_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "film_rating" ADD CONSTRAINT "film_rating_film_id_fkey" FOREIGN KEY ("film_id") REFERENCES "film"("film_id") ON DELETE RESTRICT ON UPDATE CASCADE;
