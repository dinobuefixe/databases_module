import { NextResponse } from "next/server";
import { strategies, type Strategy } from "@/lib/withdraw";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// POST /api/accounts/:id/withdraw?strategy=naive|atomic|lock  {"amount": 10}
export async function POST(request: Request, { params }: Params) {
  const id = Number((await params).id);
  const strategy = (new URL(request.url).searchParams.get("strategy") ?? "atomic") as Strategy;
  if (!(strategy in strategies)) {
    return NextResponse.json({ error: "strategy must be naive, atomic or lock" }, { status: 400 });
  }
  const body = await request.json().catch(() => ({}));
  const amount = body?.amount ?? 10;
  if (typeof amount !== "number" || amount <= 0) {
    return NextResponse.json({ error: "amount must be a positive number" }, { status: 400 });
  }

  const result = await strategies[strategy](id, amount);
  if (result.ok) return NextResponse.json({ strategy, balance: result.balance });
  const status = result.reason === "not_found" ? 404 : 409;
  return NextResponse.json({ strategy, error: result.reason }, { status });
}
