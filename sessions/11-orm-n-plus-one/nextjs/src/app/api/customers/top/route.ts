import { NextResponse } from "next/server";
import { countQueries, prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// groupBy on rental: GROUP BY customer_id ORDER BY count DESC LIMIT n, then one query for the names.
async function viaGroupBy(limit: number) {
  const counts = await prisma.rental.groupBy({
    by: ["customerId"],
    _count: { rentalId: true },
    orderBy: { _count: { rentalId: "desc" } },
    take: limit,
  });
  const customers = await prisma.customer.findMany({
    where: { customerId: { in: counts.map((c) => c.customerId) } },
    select: { customerId: true, lastName: true },
  });
  const names = new Map(customers.map((c) => [c.customerId, c.lastName]));
  return counts.map((c) => ({ customerId: c.customerId, lastName: names.get(c.customerId), rentals: c._count.rentalId }));
}

// orderBy a relation count: one query, but Prisma counts every customer's rentals before sorting.
async function viaRelation(limit: number) {
  const customers = await prisma.customer.findMany({
    take: limit,
    orderBy: { rentals: { _count: "desc" } },
    select: { customerId: true, lastName: true, _count: { select: { rentals: true } } },
  });
  return customers.map((c) => ({ customerId: c.customerId, lastName: c.lastName, rentals: c._count.rentals }));
}

// GET /api/customers/top?limit=5&via=groupBy|relation
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const limit = Math.min(Math.max(Number(params.get("limit") ?? 5) || 5, 1), 100);
  const via = params.get("via") ?? "groupBy";
  if (via !== "groupBy" && via !== "relation") {
    return NextResponse.json({ error: "via must be groupBy or relation" }, { status: 400 });
  }

  const started = performance.now();
  const { result, sql } = await countQueries(() => (via === "groupBy" ? viaGroupBy(limit) : viaRelation(limit)));
  return NextResponse.json({ via, queries: sql.length, ms: Math.round(performance.now() - started), sql, top: result });
}
