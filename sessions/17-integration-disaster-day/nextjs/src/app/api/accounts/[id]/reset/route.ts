import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// POST /api/accounts/{id}/reset {"balance": 100}: puts the account back before a concurrency test.
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid account id" }, { status: 400 });
  const body = await request.json().catch(() => ({}));
  const balance = typeof body?.balance === "number" && body.balance >= 0 ? body.balance : 100;
  const account = await prisma.account.upsert({ where: { id }, create: { id, balance }, update: { balance } });
  return NextResponse.json(account);
}
