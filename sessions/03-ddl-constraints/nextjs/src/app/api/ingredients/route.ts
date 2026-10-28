import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { violationResponse } from "@/lib/db-errors";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(await prisma.ingredient.findMany({ orderBy: { id: "asc" } }));
}

// POST /api/ingredients {"name", "kcalPer100g"}. A negative value is not checked
// here: the database rejects it with kcal_not_negative (422).
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body?.name !== "string" || typeof body?.kcalPer100g !== "number") {
    return NextResponse.json({ error: "expected name and kcalPer100g" }, { status: 400 });
  }
  try {
    const ingredient = await prisma.ingredient.create({
      data: { name: body.name, kcalPer100g: body.kcalPer100g },
    });
    return NextResponse.json(ingredient, { status: 201 });
  } catch (err) {
    return violationResponse(err);
  }
}
