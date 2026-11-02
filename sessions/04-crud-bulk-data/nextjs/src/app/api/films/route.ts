import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mpaa_rating, type Prisma } from "@/generated/prisma/client";

export const dynamic = "force-dynamic";

const SORTABLE = ["title", "length", "rental_rate", "film_id"] as const;
type SortField = (typeof SORTABLE)[number];

// GET /api/films?rating=R&q=love&sort=length&order=desc&limit=10&offset=0
// The tutorial's SELECT: WHERE rating = 'R' AND title ILIKE '%love%'
// ORDER BY length DESC LIMIT 10.
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;

  // Prisma names the enum value PG_13 because "PG-13" is not a valid identifier;
  // @map("PG-13") in the schema keeps the database value.
  const ratingParam = params.get("rating")?.replace("-", "_");
  if (ratingParam && !(ratingParam in mpaa_rating)) {
    return NextResponse.json({ error: `rating must be one of ${Object.keys(mpaa_rating).join(", ")}` }, { status: 400 });
  }
  const sort = (params.get("sort") ?? "title") as SortField;
  if (!SORTABLE.includes(sort)) {
    return NextResponse.json({ error: `sort must be one of ${SORTABLE.join(", ")}` }, { status: 400 });
  }
  const order = params.get("order") === "desc" ? "desc" : "asc";
  const limit = Math.min(Number(params.get("limit") ?? 10) || 10, 100);
  const offset = Math.max(Number(params.get("offset") ?? 0) || 0, 0);
  const q = params.get("q");

  const where: Prisma.filmWhereInput = {
    ...(ratingParam && { rating: ratingParam as mpaa_rating }),
    // mode: "insensitive" makes Prisma generate ILIKE.
    ...(q && { title: { contains: q, mode: "insensitive" } }),
  };

  const films = await prisma.film.findMany({
    where,
    select: { film_id: true, title: true, length: true, rating: true, rental_rate: true },
    // film_id as a tie-breaker gives a stable order for pagination.
    orderBy: [{ [sort]: order }, { film_id: "asc" }],
    take: limit,
    skip: offset,
  });
  return NextResponse.json(films);
}
