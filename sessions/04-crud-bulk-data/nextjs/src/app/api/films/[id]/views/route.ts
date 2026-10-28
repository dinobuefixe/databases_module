import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@/generated/prisma/client";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// POST /api/films/:id/views: count one view.
// Prisma turns this upsert into a single INSERT ... ON CONFLICT (film_id)
// DO UPDATE, because the where clause uses one unique field with the same
// value as in create. Set log: ["query"] in src/lib/prisma.ts to see it.
export async function POST(_request: Request, { params }: Params) {
  const filmId = Number((await params).id);
  if (!Number.isInteger(filmId)) return NextResponse.json({ error: "invalid film id" }, { status: 400 });
  try {
    const row = await prisma.film_views.upsert({
      where: { film_id: filmId },
      create: { film_id: filmId, views: 1 },
      update: { views: { increment: 1 } },
    });
    return NextResponse.json(row);
  } catch (err) {
    // P2003: foreign key violation, the film does not exist.
    if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2003") {
      return NextResponse.json({ error: "film not found" }, { status: 404 });
    }
    throw err;
  }
}
