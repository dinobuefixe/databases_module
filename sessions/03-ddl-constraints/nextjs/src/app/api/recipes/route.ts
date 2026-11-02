import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { violationResponse } from "@/lib/db-errors";

export const dynamic = "force-dynamic";

export async function GET() {
  const recipes = await prisma.recipe.findMany({
    include: { ingredients: true },
    orderBy: { id: "asc" },
  });
  return NextResponse.json(recipes);
}

type Line = { ingredientId: number; grams: number };

// POST /api/recipes {"authorId", "title", "servings", "ingredients": [{"ingredientId", "grams"}]}
// The handler only checks types. Servings, grams, unknown ids and repeated
// titles are left to the database constraints.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const lines: Line[] = Array.isArray(body?.ingredients) ? body.ingredients : [];
  if (
    !Number.isInteger(body?.authorId) ||
    typeof body?.title !== "string" ||
    !Number.isInteger(body?.servings) ||
    !lines.every((l) => Number.isInteger(l?.ingredientId) && typeof l?.grams === "number")
  ) {
    return NextResponse.json({ error: "expected authorId, title, servings and ingredients" }, { status: 400 });
  }
  try {
    // A nested create runs in one transaction: if one line fails, the recipe is not saved.
    const recipe = await prisma.recipe.create({
      data: {
        authorId: body.authorId,
        title: body.title,
        servings: body.servings,
        ingredients: { create: lines.map((l) => ({ ingredientId: l.ingredientId, grams: l.grams })) },
      },
      include: { ingredients: true },
    });
    return NextResponse.json(recipe, { status: 201 });
  } catch (err) {
    return violationResponse(err);
  }
}
