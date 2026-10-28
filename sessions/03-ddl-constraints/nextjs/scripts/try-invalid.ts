import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { constraintViolation } from "@/lib/db-errors";

// Break each rule on purpose and print what the database says.
async function attempt(label: string, run: () => Promise<unknown>) {
  try {
    await run();
    console.log(`ACCEPTED  ${label}`);
  } catch (err) {
    const v = constraintViolation(err);
    if (!v) throw err;
    console.log(`REJECTED  ${label}\n          ${v.constraint} (SQLSTATE ${v.sqlstate}): ${v.message}`);
  }
}

async function main() {
  console.log("Invalid inserts from the tutorial (as SQL):\n");

  await attempt("ingredient with negative calories", () =>
    prisma.$executeRaw`INSERT INTO ingredient (name, kcal_per_100g) VALUES ('Sugar', -1)`);

  await attempt("recipe for an author that does not exist", () =>
    prisma.$executeRaw`INSERT INTO recipe (author_id, title, servings) VALUES (999, 'Soup', 4)`);

  await attempt("two authors with the same email", () =>
    prisma.$executeRaw`INSERT INTO author (name, email) VALUES ('Ana', 'twin@example.com'), ('Ana 2', 'twin@example.com')`);

  // A small fixture of our own, so the script does not depend on the seed.
  const author = await prisma.author.create({
    data: { name: "Constraint tester", email: `tester-${Date.now()}@example.com` },
  });
  const ingredient = await prisma.ingredient.upsert({
    where: { name: "Water" },
    update: {},
    create: { name: "Water", kcalPer100g: 0 },
  });

  await attempt("recipe with 0 servings", () =>
    prisma.$executeRaw`INSERT INTO recipe (author_id, title, servings) VALUES (${author.id}, 'Nothing', 0)`);

  const recipe = await prisma.recipe.create({
    data: {
      authorId: author.id,
      title: "Glass of water",
      servings: 1,
      ingredients: { create: [{ ingredientId: ingredient.id, grams: 250 }] },
    },
  });

  await attempt("same author, same title", () =>
    prisma.$executeRaw`INSERT INTO recipe (author_id, title, servings) VALUES (${author.id}, 'Glass of water', 2)`);

  await attempt("recipe line with 0 grams", () =>
    prisma.$executeRaw`UPDATE recipe_ingredient SET grams = 0 WHERE recipe_id = ${recipe.id}`);

  console.log("\nON DELETE behaviour:\n");

  await attempt("delete an author who has recipes (RESTRICT)", () =>
    prisma.author.delete({ where: { id: author.id } }));

  await attempt("delete an ingredient used by a recipe (RESTRICT)", () =>
    prisma.ingredient.delete({ where: { id: ingredient.id } }));

  const before = await prisma.recipeIngredient.count({ where: { recipeId: recipe.id } });
  await attempt("delete the recipe (CASCADE)", () => prisma.recipe.delete({ where: { id: recipe.id } }));
  const after = await prisma.recipeIngredient.count({ where: { recipeId: recipe.id } });
  console.log(`          recipe_ingredient lines for recipe ${recipe.id}: ${before} before, ${after} after`);

  await attempt("delete the author now that they have no recipes", () =>
    prisma.author.delete({ where: { id: author.id } }));
  await attempt("delete the ingredient now that no recipe uses it", () =>
    prisma.ingredient.delete({ where: { id: ingredient.id } }));
}

main().finally(() => prisma.$disconnect());
