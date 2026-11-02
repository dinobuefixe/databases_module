import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/customers/by-email?email=MARY.SMITH@sakilacustomer.org
export async function GET(request: Request) {
  const email = new URL(request.url).searchParams.get("email");
  if (!email) return NextResponse.json({ error: "email is required" }, { status: 400 });

  const rows = await prisma.$queryRaw<{ customer_id: number; first_name: string; last_name: string }[]>`
    SELECT customer_id, first_name, last_name
    FROM customer
    WHERE lower(email) = lower(${email})`;
  if (rows.length === 0) return NextResponse.json({ error: "Customer not found" }, { status: 404 });
  return NextResponse.json(rows[0]);
}
