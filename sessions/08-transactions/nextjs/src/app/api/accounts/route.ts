import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/accounts
export async function GET() {
  return NextResponse.json(await prisma.account.findMany({ orderBy: { id: "asc" } }));
}
