import { NextResponse } from "next/server";
import { leaderboardKey } from "@/lib/leaderboard";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/leaderboard/customers?week=2026-W41: the top 10 of that week (default: this week).
// ZRANGE key 0 9 REV WITHSCORES, the same as ZREVRANGE key 0 9 WITHSCORES.
export async function GET(request: Request) {
  const week = new URL(request.url).searchParams.get("week");
  if (week !== null && !/^\d{4}-W\d{2}$/.test(week)) {
    return NextResponse.json({ error: "week must look like 2026-W41" }, { status: 400 });
  }
  const key = leaderboardKey(week ?? undefined);
  const redis = await getRedis();
  const top = await redis.zRangeWithScores(key, 0, 9, { REV: true });
  return NextResponse.json({
    key,
    ttl: await redis.ttl(key),
    top: top.map(({ value, score }, i) => ({ rank: i + 1, member: value, rentals: score })),
  });
}
