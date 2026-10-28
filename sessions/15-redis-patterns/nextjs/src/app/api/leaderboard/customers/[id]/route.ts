import { NextResponse } from "next/server";
import { leaderboardKey, recordRental } from "@/lib/leaderboard";
import { parseId } from "@/lib/params";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// ZREVRANK counts from 0 for the highest score, and returns null for a member not in the set.
async function rankOf(key: string, member: string) {
  const redis = await getRedis();
  const rank = await redis.zRevRank(key, member);
  if (rank === null) return NextResponse.json({ error: `${member} is not in ${key}` }, { status: 404 });
  return NextResponse.json({ key, member, rank: rank + 1, rentals: await redis.zScore(key, member) });
}

// POST /api/leaderboard/customers/{id}: records one rental for the customer this week.
export async function POST(_request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const { key } = await recordRental(await getRedis(), id);
  return rankOf(key, `customer:${id}`);
}

// GET /api/leaderboard/customers/{id}?week=2026-W41: the customer's rank and score that week.
export async function GET(request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const week = new URL(request.url).searchParams.get("week");
  if (week !== null && !/^\d{4}-W\d{2}$/.test(week)) {
    return NextResponse.json({ error: "week must look like 2026-W41" }, { status: 400 });
  }
  return rankOf(leaderboardKey(week ?? undefined), `customer:${id}`);
}
