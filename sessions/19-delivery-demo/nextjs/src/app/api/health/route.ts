import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/health: the first thing to show in the demo, and what clean-clone-check waits for.
export async function GET() {
  const check = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      return "ok";
    } catch (err) {
      return `error: ${(err as Error).message}`;
    }
  };
  const result = {
    postgres: await check(() => prisma.$queryRaw`SELECT 1`),
    redis: await check(async () => (await getRedis()).ping()),
  };
  const healthy = Object.values(result).every((v) => v === "ok");
  return NextResponse.json(result, { status: healthy ? 200 : 503 });
}
