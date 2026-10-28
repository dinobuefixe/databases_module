import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/films/longest-per-rating?top=2
// Top N per group: rank inside each rating, then filter in the outer query.
// DENSE_RANK gives tied films the same position, so a rating can return more
// than N films. A window function cannot go in WHERE, hence the CTE.
export async function GET(request: Request) {
  const top = Number(new URL(request.url).searchParams.get("top") ?? 2);
  if (!Number.isInteger(top) || top < 1) {
    return NextResponse.json({ error: "top must be a positive integer" }, { status: 400 });
  }
  const rows = await prisma.$queryRaw`
    WITH ranked AS (
        SELECT title, rating, length,
               DENSE_RANK() OVER (PARTITION BY rating ORDER BY length DESC) AS pos
        FROM film
    )
    SELECT title, rating::text AS rating, length, pos::int AS pos
    FROM ranked
    WHERE pos <= ${top}
    ORDER BY rating, pos, title`;
  return NextResponse.json(rows);
}
