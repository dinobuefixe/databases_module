import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// GET /api/customers/:id/payments
// Running total: SUM(...) OVER (... ORDER BY payment_date) adds each payment
// to the ones before it, and keeps every row (GROUP BY would collapse them).
export async function GET(_request: Request, { params }: Params) {
  const customerId = Number((await params).id);
  if (!Number.isInteger(customerId)) return NextResponse.json({ error: "invalid id" }, { status: 400 });
  const rows = await prisma.$queryRaw`
    SELECT customer_id, payment_date, amount,
           SUM(amount) OVER (PARTITION BY customer_id ORDER BY payment_date) AS running_total
    FROM payment
    WHERE customer_id = ${customerId}
    ORDER BY customer_id, payment_date`;
  return NextResponse.json(rows);
}
