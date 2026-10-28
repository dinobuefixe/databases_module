import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

const today = () => new Date().toISOString().slice(0, 10);

// POST /api/visitors {"customer_id": 5}: SADD ignores members already in the set.
export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!Number.isInteger(body?.customer_id)) {
    return NextResponse.json({ error: "customer_id must be an integer" }, { status: 400 });
  }
  const key = `visitors:${today()}`;
  const redis = await getRedis();
  const added = await redis.sAdd(key, `customer:${body.customer_id}`);
  return NextResponse.json({ key, added, unique: await redis.sCard(key) });
}

// GET /api/visitors?date=YYYY-MM-DD: SCARD counts unique visitors without reading them.
export async function GET(request: Request) {
  const date = new URL(request.url).searchParams.get("date") ?? today();
  const key = `visitors:${date}`;
  return NextResponse.json({ key, unique: await (await getRedis()).sCard(key) });
}
