import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/accounts/{id}
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = Number((await params).id);
  const account = Number.isInteger(id) ? await prisma.account.findUnique({ where: { id } }) : null;
  if (!account) return NextResponse.json({ error: "Account not found" }, { status: 404 });
  return NextResponse.json(account);
}
