import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// POST /api/accounts/{id}/withdraw {"amount": 10}
// Rule: the balance never goes below 0, however many requests arrive at once.
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid account id" }, { status: 400 });
  const body = await request.json().catch(() => ({}));
  const amount = body?.amount ?? 10;
  if (typeof amount !== "number" || !(amount > 0)) {
    return NextResponse.json({ error: "amount must be a positive number" }, { status: 422 });
  }

  // One atomic conditional UPDATE (session 08, fix 1):
  // UPDATE account SET balance = balance - $1 WHERE id = $2 AND balance >= $1
  const { count } = await prisma.account.updateMany({
    where: { id, balance: { gte: amount } },
    data: { balance: { decrement: amount } },
  });
  if (count === 0) {
    const exists = await prisma.account.count({ where: { id } });
    return exists
      ? NextResponse.json({ error: "Insufficient balance" }, { status: 409 })
      : NextResponse.json({ error: "Account not found" }, { status: 404 });
  }
  return NextResponse.json({ id, withdrawn: amount });
}
