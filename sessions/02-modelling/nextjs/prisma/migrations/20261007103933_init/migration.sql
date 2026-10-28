-- CreateTable
CREATE TABLE "author" (
    "author_id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,

    CONSTRAINT "author_pkey" PRIMARY KEY ("author_id")
);

-- CreateTable
CREATE TABLE "recipe" (
    "recipe_id" SERIAL NOT NULL,
    "author_id" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "servings" INTEGER NOT NULL,
    "kcal_per_serving" DECIMAL(7,1) NOT NULL DEFAULT 0,

    CONSTRAINT "recipe_pkey" PRIMARY KEY ("recipe_id")
);

-- CreateTable
CREATE TABLE "ingredient" (
    "ingredient_id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "kcal_per_100g" DECIMAL(6,1) NOT NULL,

    CONSTRAINT "ingredient_pkey" PRIMARY KEY ("ingredient_id")
);

-- CreateTable
CREATE TABLE "recipe_ingredient" (
    "recipe_id" INTEGER NOT NULL,
    "ingredient_id" INTEGER NOT NULL,
    "grams" DECIMAL(7,1) NOT NULL,

    CONSTRAINT "recipe_ingredient_pkey" PRIMARY KEY ("recipe_id","ingredient_id")
);

-- AddForeignKey
ALTER TABLE "recipe" ADD CONSTRAINT "recipe_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "author"("author_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recipe_ingredient" ADD CONSTRAINT "recipe_ingredient_recipe_id_fkey" FOREIGN KEY ("recipe_id") REFERENCES "recipe"("recipe_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recipe_ingredient" ADD CONSTRAINT "recipe_ingredient_ingredient_id_fkey" FOREIGN KEY ("ingredient_id") REFERENCES "ingredient"("ingredient_id") ON DELETE RESTRICT ON UPDATE CASCADE;
