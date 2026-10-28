import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";
import { refreshFilmRating } from "@/lib/ratings";

export const dynamic = "force-dynamic";

// POST /api/films/{id}/ratings {"customer_id": 1, "stars": 4}
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const filmId = parseId((await params).id);
  if (filmId === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const body = await request.json().catch(() => null);
  const { customer_id, stars } = body ?? {};
  if (!Number.isInteger(customer_id) || !Number.isInteger(stars) || stars < 1 || stars > 5) {
    return NextResponse.json({ error: "customer_id and stars (1 to 5) are required" }, { status: 422 });
  }

  const rating = await prisma.film_rating.upsert({
    where: { customer_id_film_id: { customer_id, film_id: filmId } },
    create: { customer_id, film_id: filmId, stars },
    update: { stars },
  });
  await refreshFilmRating(filmId);

  return NextResponse.json(rating, { status: 201 });
}
