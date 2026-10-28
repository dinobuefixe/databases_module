-- Generated with `prisma migrate dev --create-only`, then edited by hand:
-- identity columns instead of SERIAL, and the CHECK constraints at the end.

-- CreateTable
CREATE TABLE "author" (
    "author_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "author_pkey" PRIMARY KEY ("author_id")
);

-- CreateTable
CREATE TABLE "ingredient" (
    "ingredient_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "name" TEXT NOT NULL,
    "kcal_per_100g" DECIMAL(6,1) NOT NULL,

    CONSTRAINT "ingredient_pkey" PRIMARY KEY ("ingredient_id")
);

-- CreateTable
CREATE TABLE "recipe" (
    "recipe_id" INTEGER GENERATED ALWAYS AS IDENTITY,
    "author_id" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "servings" INTEGER NOT NULL,
    "published_at" TIMESTAMPTZ,

    CONSTRAINT "recipe_pkey" PRIMARY KEY ("recipe_id")
);

-- CreateTable
CREATE TABLE "recipe_ingredient" (
    "recipe_id" INTEGER NOT NULL,
    "ingredient_id" INTEGER NOT NULL,
    "grams" DECIMAL(7,1) NOT NULL,

    CONSTRAINT "recipe_ingredient_pkey" PRIMARY KEY ("recipe_id","ingredient_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "author_email_key" ON "author"("email");

-- CreateIndex
CREATE UNIQUE INDEX "ingredient_name_key" ON "ingredient"("name");

-- CreateIndex
CREATE UNIQUE INDEX "recipe_author_id_title_key" ON "recipe"("author_id", "title");

-- AddForeignKey
ALTER TABLE "recipe" ADD CONSTRAINT "recipe_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "author"("author_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recipe_ingredient" ADD CONSTRAINT "recipe_ingredient_recipe_id_fkey" FOREIGN KEY ("recipe_id") REFERENCES "recipe"("recipe_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recipe_ingredient" ADD CONSTRAINT "recipe_ingredient_ingredient_id_fkey" FOREIGN KEY ("ingredient_id") REFERENCES "ingredient"("ingredient_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- Added by hand: Prisma's schema cannot express CHECK constraints.
-- Named constraints give clearer error messages in the application.
ALTER TABLE "ingredient" ADD CONSTRAINT "kcal_not_negative" CHECK ("kcal_per_100g" >= 0);
ALTER TABLE "recipe" ADD CONSTRAINT "servings_between_1_and_50" CHECK ("servings" BETWEEN 1 AND 50);
ALTER TABLE "recipe_ingredient" ADD CONSTRAINT "grams_positive" CHECK ("grams" > 0);
