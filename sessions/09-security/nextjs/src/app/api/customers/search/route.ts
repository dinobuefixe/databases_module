import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/customers/search?email=...
// Safe: the tagged template sends the SQL text and the value separately
// ($1 and a parameter). The database never reads the value as SQL.
export async function GET(request: Request) {
  const email = new URL(request.url).searchParams.get("email") ?? "";
  const rows = await prisma.$queryRaw<{ customer_id: number }[]>`
    SELECT customer_id, first_name, last_name, email FROM customer WHERE email = ${email}`;
  return NextResponse.json({ count: rows.length, rows: rows.slice(0, 5) });
}
