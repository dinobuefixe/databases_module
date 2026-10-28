import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/customers/search?q=smith
export async function GET(request: Request) {
  const q = new URL(request.url).searchParams.get("q") ?? "";
  if (q.length < 2) return NextResponse.json({ error: "q must have at least 2 characters" }, { status: 400 });

  const customers = await prisma.$queryRawUnsafe(
    `SELECT customer_id, first_name, last_name, email
     FROM customer
     WHERE last_name ILIKE '%${q}%'
     ORDER BY last_name, first_name
     LIMIT 20`,
  );
  return NextResponse.json(customers);
}
