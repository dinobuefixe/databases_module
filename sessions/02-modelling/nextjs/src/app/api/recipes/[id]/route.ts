import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// GET /api/recipes/:id: the detail page joins the author and the ingredients.
export async function GET(_request: Request, { params }: Params) {
  const id = Number((await params).id);
  const recipe = await prisma.recipe.findUnique({
    where: { id },
    include: {
      author: true,
      ingredients: { include: { ingredient: true }, orderBy: { ingredientId: "asc" } },
    },
  });
  if (!recipe) return NextResponse.json({ error: "recipe not found" }, { status: 404 });
  return NextResponse.json(recipe);
}

// DELETE /api/recipes/:id: removes the recipe and its lines. The author and
// the ingredients stay, because they live in their own tables.
export async function DELETE(_request: Request, { params }: Params) {
  const id = Number((await params).id);
  const deleted = await prisma.$transaction(async (tx) => {
    // No ON DELETE CASCADE yet (session 03), so delete the lines first.
    await tx.recipeIngredient.deleteMany({ where: { recipeId: id } });
    return tx.recipe.deleteMany({ where: { id } });
  });
  if (deleted.count === 0) return NextResponse.json({ error: "recipe not found" }, { status: 404 });
  return new NextResponse(null, { status: 204 });
}
