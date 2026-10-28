import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// DELETE /api/recipes/:id. ON DELETE CASCADE removes the recipe's lines in
// recipe_ingredient; the application does not delete them itself.
export async function DELETE(_request: Request, { params }: Params) {
  const id = Number((await params).id);
  const lines = await prisma.recipeIngredient.count({ where: { recipeId: id } });
  const { count } = await prisma.recipe.deleteMany({ where: { id } });
  if (count === 0) return NextResponse.json({ error: "recipe not found" }, { status: 404 });
  return NextResponse.json({ deletedRecipe: id, linesRemovedByCascade: lines });
}
