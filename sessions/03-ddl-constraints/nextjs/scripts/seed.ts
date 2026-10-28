import "dotenv/config";
import { prisma } from "@/lib/prisma";

// The tutorial's recipes. Empties the tables first so it can be run again.
async function main() {
  await prisma.$transaction(async (tx) => {
    await tx.$executeRaw`TRUNCATE recipe_ingredient, recipe, ingredient, author RESTART IDENTITY`;

    const ana = await tx.author.create({ data: { name: "Ana", email: "ana@example.com" } });
    const rui = await tx.author.create({ data: { name: "Rui", email: "rui@example.com" } });
    const flour = await tx.ingredient.create({ data: { name: "Flour", kcalPer100g: 364 } });
    const milk = await tx.ingredient.create({ data: { name: "Milk", kcalPer100g: 42 } });
    const egg = await tx.ingredient.create({ data: { name: "Egg", kcalPer100g: 155 } });

    await tx.recipe.create({
      data: {
        authorId: ana.id,
        title: "Pancakes",
        servings: 4,
        ingredients: {
          create: [
            { ingredientId: flour.id, grams: 200 },
            { ingredientId: milk.id, grams: 300 },
          ],
        },
      },
    });
    await tx.recipe.create({
      data: {
        authorId: rui.id,
        title: "Omelette",
        servings: 1,
        ingredients: { create: [{ ingredientId: egg.id, grams: 120 }] },
      },
    });
  });
  console.log("Seeded 2 authors, 3 ingredients, 2 recipes");
}

main().finally(() => prisma.$disconnect());
