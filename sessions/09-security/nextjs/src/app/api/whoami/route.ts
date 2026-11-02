import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { mongo } from "@/lib/mongo";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// GET /api/whoami: which user the application is connected as on each engine.
// None of them should be a superuser or root.
export async function GET() {
  const [pg] = await prisma.$queryRaw<{ user: string; superuser: boolean }[]>`
    SELECT current_user AS user, rolsuper AS superuser FROM pg_roles WHERE rolname = current_user`;
  const status = await mongo.db(process.env.MONGO_DB).command({ connectionStatus: 1 });
  const redis = await getRedis();
  return NextResponse.json({
    postgres: pg,
    mongo: status.authInfo.authenticatedUserRoles,
    redis: String(await redis.sendCommand(["ACL", "WHOAMI"])),
  });
}
