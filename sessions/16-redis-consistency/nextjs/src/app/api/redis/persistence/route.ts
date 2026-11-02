import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/redis/persistence: reads the server's persistence and memory settings.
// CONFIG GET only reads. Change them in redis.conf or docker-compose.yml, not with CONFIG SET.
export async function GET() {
  const redis = await getRedis();
  const config = await redis.configGet(["appendonly", "appendfsync", "save", "maxmemory", "maxmemory-policy"]);
  return NextResponse.json({
    current: config,
    recommended: { appendonly: "yes", appendfsync: "everysec", maxmemory: "256mb", "maxmemory-policy": "noeviction" },
  });
}
