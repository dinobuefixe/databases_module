import { NextResponse } from "next/server";
import { resetAccounts } from "@/lib/withdraw";

export const dynamic = "force-dynamic";

// POST /api/accounts/reset {"balance": 100}: accounts 1 and 2 back to a known balance.
export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const balance = body?.balance ?? 100;
  if (typeof balance !== "number" || balance < 0) {
    return NextResponse.json({ error: "balance must be a number >= 0" }, { status: 400 });
  }
  return NextResponse.json(await resetAccounts(balance));
}
