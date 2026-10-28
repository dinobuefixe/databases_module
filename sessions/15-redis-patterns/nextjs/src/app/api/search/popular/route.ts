import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/search/popular: ZRANGE search:terms 0 4 REV WITHSCORES.
export async function GET() {
  const terms = await (await getRedis()).zRangeWithScores("search:terms", 0, 4, { REV: true });
  return NextResponse.json(terms);
}
