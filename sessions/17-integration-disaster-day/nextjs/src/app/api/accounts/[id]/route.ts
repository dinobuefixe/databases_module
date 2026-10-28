import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/accounts/{id}
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid account id" }, { status: 400 });
  const account = await prisma.account.findUnique({ where: { id } });
  if (!account) return NextResponse.json({ error: "Account not found" }, { status: 404 });
  return NextResponse.json(account);
}
