import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// UNSAFE, for a local demonstration only. Never write code like this.
// GET /api/customers/search-unsafe?email=...
// The input is pasted into the SQL text, so it becomes code. With
// email = ' OR '1'='1 the WHERE clause is always true and every customer comes back.
// $queryRawUnsafe exists for SQL built at run time; it does no escaping.
export async function GET(request: Request) {
  const email = new URL(request.url).searchParams.get("email") ?? "";
  const sql = `SELECT customer_id, first_name, last_name, email FROM customer WHERE email = '${email}'`;
  const rows = await prisma.$queryRawUnsafe<{ customer_id: number }[]>(sql);
  return NextResponse.json({ sql, count: rows.length, rows: rows.slice(0, 5) });
}
