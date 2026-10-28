import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { recalculateKcal } from "@/lib/recipes";

// The three spreadsheet rows from the tutorial, normalised:
// each author, ingredient and recipe once, plus one line per recipe-ingredient pair.
async function main() {
  await prisma.$transaction(async (tx) => {
    // Start from empty tables so the seed can be run again.
    await tx.$executeRaw`TRUNCATE recipe_ingredient, recipe, ingredient, author RESTART IDENTITY`;

    const ana = await tx.author.create({ data: { name: "Ana", email: "ana@example.com" } });
    const rui = await tx.author.create({ data: { name: "Rui", email: "rui@example.com" } });

    const flour = await tx.ingredient.create({ data: { name: "Flour", kcalPer100g: 364 } });
    const milk = await tx.ingredient.create({ data: { name: "Milk", kcalPer100g: 42 } });
    const egg = await tx.ingredient.create({ data: { name: "Egg", kcalPer100g: 155 } });

    // The spreadsheet has no servings column; these values are our choice.
    const pancakes = await tx.recipe.create({
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
    const omelette = await tx.recipe.create({
      data: {
        authorId: rui.id,
        title: "Omelette",
        servings: 1,
        ingredients: { create: [{ ingredientId: egg.id, grams: 120 }] },
      },
    });

    await recalculateKcal(tx, pancakes.id);
    await recalculateKcal(tx, omelette.id);
  });

  const recipes = await prisma.recipe.findMany({ orderBy: { id: "asc" } });
  console.table(recipes.map((r) => ({ ...r, kcalPerServing: r.kcalPerServing.toString() })));
}

main().finally(() => prisma.$disconnect());
