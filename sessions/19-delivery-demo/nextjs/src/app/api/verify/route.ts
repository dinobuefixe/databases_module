import { NextResponse } from "next/server";
import { verify } from "@/lib/films-sets";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/verify: Redis sets against PostgreSQL. 200 when they match, 409 when not.
export async function GET() {
  const result = await verify(await getRedis());
  return NextResponse.json({ ok: result.mismatches === 0, ...result }, { status: result.mismatches ? 409 : 200 });
}
