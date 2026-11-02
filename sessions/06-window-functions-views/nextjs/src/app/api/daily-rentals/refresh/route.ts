import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// POST /api/daily-rentals/refresh
// CONCURRENTLY rebuilds the view while readers keep reading the old rows.
// It needs the unique index created in the migration, and it cannot run
// inside a transaction block.
export async function POST() {
  const start = performance.now();
  await prisma.$executeRaw`REFRESH MATERIALIZED VIEW CONCURRENTLY daily_rentals`;
  const ms = Math.round(performance.now() - start);
  const [{ days, rentals }] = await prisma.$queryRaw<{ days: number; rentals: number }[]>`
    SELECT count(*)::int AS days, sum(rentals)::int AS rentals FROM daily_rentals`;
  return NextResponse.json({ refreshed: true, ms, days, rentals });
}
