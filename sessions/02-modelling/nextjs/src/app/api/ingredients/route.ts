import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/ingredients
export async function GET() {
  return NextResponse.json(await prisma.ingredient.findMany({ orderBy: { id: "asc" } }));
}

// POST /api/ingredients {"name", "kcalPer100g"}: an ingredient can exist before
// any recipe uses it (no insertion anomaly).
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (typeof body?.name !== "string" || !body.name.trim() || typeof body?.kcalPer100g !== "number") {
    return NextResponse.json({ error: "expected name and kcalPer100g" }, { status: 400 });
  }
  const ingredient = await prisma.ingredient.create({
    data: { name: body.name.trim(), kcalPer100g: body.kcalPer100g },
  });
  return NextResponse.json(ingredient, { status: 201 });
}
