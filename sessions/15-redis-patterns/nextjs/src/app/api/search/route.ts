import { NextResponse } from "next/server";
import { allowRequest } from "@/lib/patterns";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/search?q=alien: searches film titles, counts the term, and is rate limited.
export async function GET(request: Request) {
  const redis = await getRedis();

  // The client is identified by a header here; behind a proxy you would use the client's IP.
  const clientId = request.headers.get("x-client-id") ?? "anonymous";
  const limit = await allowRequest(redis, clientId);
  const headers = { "x-ratelimit-limit": String(limit.limit), "x-ratelimit-count": String(limit.count) };
  if (!limit.allowed) {
    return NextResponse.json({ error: "Too many requests, try again next minute" }, { status: 429, headers });
  }

  const q = (new URL(request.url).searchParams.get("q") ?? "").trim().toLowerCase();
  if (!q) return NextResponse.json({ error: "q is required" }, { status: 400, headers });

  // ZINCRBY adds 1 to the term's score, creating it with score 1 the first time.
  await redis.zIncrBy("search:terms", 1, q);
  const films = await prisma.film.findMany({
    where: { title: { contains: q, mode: "insensitive" } },
    select: { film_id: true, title: true },
    take: 10,
  });
  return NextResponse.json({ q, films }, { headers });
}
