import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { ratingKey } from "@/lib/ratings";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/films/{id}/rating
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const filmId = parseId((await params).id);
  if (filmId === null) return NextResponse.json({ error: "Invalid film id" }, { status: 400 });
  const rating = await (await getRedis()).hGetAll(ratingKey(filmId));
  return NextResponse.json({
    film_id: filmId,
    average: Number(rating.average ?? 0),
    count: Number(rating.count ?? 0),
  });
}
