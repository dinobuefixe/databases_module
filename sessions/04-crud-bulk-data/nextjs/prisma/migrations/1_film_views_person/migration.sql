-- CreateTable
CREATE TABLE "film_views" (
    "film_id" INTEGER NOT NULL,
    "views" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "film_views_pkey" PRIMARY KEY ("film_id")
);

-- CreateTable
CREATE TABLE "person" (
    "person_id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "city" TEXT NOT NULL,

    CONSTRAINT "person_pkey" PRIMARY KEY ("person_id")
);

-- AddForeignKey
ALTER TABLE "film_views" ADD CONSTRAINT "film_views_film_id_fkey" FOREIGN KEY ("film_id") REFERENCES "film"("film_id") ON DELETE RESTRICT ON UPDATE CASCADE;
