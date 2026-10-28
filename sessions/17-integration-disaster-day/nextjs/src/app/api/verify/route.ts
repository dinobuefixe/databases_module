import { NextResponse } from "next/server";
import { verify } from "@/lib/films-sets";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/verify: Redis sets against PostgreSQL. 200 when they match, 409 when not.
export async function GET() {
  const { checked, mismatches } = await verify(await getRedis());
  const ok = mismatches.length === 0;
  return NextResponse.json({ ok, checked, mismatches: mismatches.length, sample: mismatches.slice(0, 10) }, {
    status: ok ? 200 : 409,
  });
}
