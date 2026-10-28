import { Prisma } from "@/generated/prisma/client";

export type Line = { ingredientId: number; grams: number };

// Recalculate the stored kcal_per_serving of one recipe. Always call it inside
// the transaction that changed the ingredients, so the stored value cannot
// disagree with the ingredient list.
export async function recalculateKcal(tx: Prisma.TransactionClient, recipeId: number) {
  const recipe = await tx.recipe.findUniqueOrThrow({
    where: { id: recipeId },
    include: { ingredients: { include: { ingredient: true } } },
  });
  const total = recipe.ingredients.reduce(
    (sum, line) => sum.plus(line.grams.times(line.ingredient.kcalPer100g).dividedBy(100)),
    new Prisma.Decimal(0),
  );
  const kcalPerServing = total.dividedBy(recipe.servings).toDecimalPlaces(1);
  return tx.recipe.update({ where: { id: recipeId }, data: { kcalPerServing } });
}

// Minimal request validation. Session 03 moves these rules into the database.
export function parseLines(value: unknown): Line[] | null {
  if (!Array.isArray(value) || value.length === 0) return null;
  const lines: Line[] = [];
  for (const item of value) {
    if (!Number.isInteger(item?.ingredientId) || typeof item?.grams !== "number" || item.grams <= 0) {
      return null;
    }
    lines.push({ ingredientId: item.ingredientId, grams: item.grams });
  }
  return lines;
}

// P2003 is Prisma's code for a foreign key violation: the author or an
// ingredient id does not exist.
export function isMissingReference(err: unknown): boolean {
  return err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2003";
}
