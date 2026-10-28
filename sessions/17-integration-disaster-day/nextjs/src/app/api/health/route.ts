import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mongoDb } from "@/lib/mongo";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

async function check(fn: () => Promise<unknown>): Promise<string> {
  try {
    await fn();
    return "ok";
  } catch (err) {
    return `error: ${(err as Error).message}`;
  }
}

// GET /api/health: one cheap command per engine.
export async function GET() {
  const result = {
    postgres: await check(() => prisma.$queryRaw`SELECT 1`),
    mongo: await check(() => mongoDb().command({ ping: 1 })),
    redis: await check(async () => (await getRedis()).ping()),
  };
  const healthy = Object.values(result).every((v) => v === "ok");
  return NextResponse.json(result, { status: healthy ? 200 : 503 });
}
