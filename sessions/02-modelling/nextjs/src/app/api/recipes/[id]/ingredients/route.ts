import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { isMissingReference, parseLines, recalculateKcal } from "@/lib/recipes";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// PUT /api/recipes/:id/ingredients [{"ingredientId", "grams"}, ...]
// Replaces the ingredient list and recalculates kcal_per_serving in the same
// transaction. This is the cost of the denormalisation: every write path that
// changes the ingredients must also update the stored value.
export async function PUT(request: Request, { params }: Params) {
  const id = Number((await params).id);
  const lines = parseLines(await request.json().catch(() => null));
  if (!lines) {
    return NextResponse.json({ error: "expected a non-empty list of {ingredientId, grams}" }, { status: 400 });
  }

  const exists = await prisma.recipe.findUnique({ where: { id }, select: { id: true } });
  if (!exists) return NextResponse.json({ error: "recipe not found" }, { status: 404 });

  try {
    const recipe = await prisma.$transaction(async (tx) => {
      await tx.recipeIngredient.deleteMany({ where: { recipeId: id } });
      await tx.recipeIngredient.createMany({ data: lines.map((l) => ({ recipeId: id, ...l })) });
      return recalculateKcal(tx, id);
    });
    return NextResponse.json(recipe);
  } catch (err) {
    if (isMissingReference(err)) {
      return NextResponse.json({ error: "an ingredientId does not exist" }, { status: 400 });
    }
    throw err;
  }
}
