import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/authors: each author once, with the number of recipes they wrote.
export async function GET() {
  const authors = await prisma.author.findMany({
    include: { _count: { select: { recipes: true } } },
    orderBy: { id: "asc" },
  });
  return NextResponse.json(authors);
}
