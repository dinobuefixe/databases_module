import { NextResponse } from "next/server";
import { withdrawAtomic } from "@/lib/withdraw";

export const dynamic = "force-dynamic";

// POST /api/accounts/{id}/withdraw {"amount": 10}: the atomic version from the demo.
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = Number((await params).id);
  const body = await request.json().catch(() => ({}));
  const amount = body?.amount ?? 10;
  if (!Number.isInteger(id) || typeof amount !== "number" || !(amount > 0)) {
    return NextResponse.json({ error: "Invalid account id or amount" }, { status: 422 });
  }
  if (!(await withdrawAtomic(id, amount))) {
    return NextResponse.json({ error: "Insufficient balance or unknown account" }, { status: 409 });
  }
  return NextResponse.json({ id, withdrawn: amount });
}
