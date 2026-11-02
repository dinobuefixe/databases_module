import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/daily-rentals?from=2022-05-01&days=31
// Reads the materialised view: stored rows, no GROUP BY over rental at read time.
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const from = params.get("from") ?? "1900-01-01";
  const days = Math.min(Number(params.get("days") ?? 31) || 31, 366);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(from)) {
    return NextResponse.json({ error: "from must be YYYY-MM-DD" }, { status: 400 });
  }
  const rows = await prisma.$queryRaw`
    SELECT day::text AS day, rentals::int AS rentals
    FROM daily_rentals
    WHERE day >= ${from}::date
    ORDER BY day
    LIMIT ${days}`;
  return NextResponse.json(rows);
}
