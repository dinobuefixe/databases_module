import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { isMissingReference, parseLines, recalculateKcal } from "@/lib/recipes";

export const dynamic = "force-dynamic";

// GET /api/recipes: the listing page. It reads the stored kcal_per_serving,
// so it needs one query on one table, with no join and no SUM.
export async function GET() {
  const recipes = await prisma.recipe.findMany({
    select: { id: true, title: true, servings: true, kcalPerServing: true },
    orderBy: { id: "asc" },
  });
  return NextResponse.json(recipes);
}

// POST /api/recipes {"authorId", "title", "servings", "ingredients": [{"ingredientId", "grams"}]}
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const lines = parseLines(body?.ingredients);
  if (
    !Number.isInteger(body?.authorId) ||
    typeof body?.title !== "string" ||
    !body.title.trim() ||
    !Number.isInteger(body?.servings) ||
    !lines
  ) {
    return NextResponse.json(
      { error: "expected authorId, title, servings and a non-empty ingredients list" },
      { status: 400 },
    );
  }

  try {
    // One transaction: the recipe, its lines and the recalculated kcal are
    // saved together or not at all.
    const recipe = await prisma.$transaction(async (tx) => {
      const created = await tx.recipe.create({
        data: {
          authorId: body.authorId,
          title: body.title.trim(),
          servings: body.servings,
          ingredients: { create: lines },
        },
      });
      return recalculateKcal(tx, created.id);
    });
    return NextResponse.json(recipe, { status: 201 });
  } catch (err) {
    if (isMissingReference(err)) {
      return NextResponse.json({ error: "authorId or an ingredientId does not exist" }, { status: 400 });
    }
    throw err;
  }
}
