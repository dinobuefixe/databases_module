import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };

// GET /api/customers/:id/rental-gaps
// LAG reads the previous row of the same customer, so each rental can be
// compared with the one before it. The first rental has no previous row: NULL.
export async function GET(_request: Request, { params }: Params) {
  const customerId = Number((await params).id);
  if (!Number.isInteger(customerId)) return NextResponse.json({ error: "invalid id" }, { status: 400 });
  // gap is an interval. $queryRaw cannot deserialise intervals, so we cast it
  // to text ("3 days 02:15:00") and also return it in days as a number.
  const rows = await prisma.$queryRaw`
    WITH gaps AS (
        SELECT customer_id, rental_date,
               rental_date - LAG(rental_date) OVER (PARTITION BY customer_id ORDER BY rental_date) AS gap
        FROM rental
        WHERE customer_id = ${customerId}
    )
    SELECT customer_id, rental_date, gap::text AS gap,
           round((extract(epoch FROM gap) / 86400)::numeric, 2)::float8 AS gap_days
    FROM gaps
    ORDER BY rental_date`;
  return NextResponse.json(rows);
}
