import { NextResponse } from "next/server";
import { countQueries, prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

type Strategy = "query" | "join" | "count";

// N+1: one query for the customers, then one more per customer.
async function lazy(limit: number) {
  const customers = await prisma.customer.findMany({ take: limit, orderBy: { customerId: "asc" } });
  const result = [];
  for (const c of customers) {
    const rentals = await prisma.rental.findMany({ where: { customerId: c.customerId } });
    result.push({ customerId: c.customerId, firstName: c.firstName, rentals: rentals.length });
  }
  return result;
}

// Eager loading: the rentals come with the customers.
async function eager(limit: number, strategy: Strategy) {
  if (strategy === "count") {
    // Only the number is needed, so ask the database for the number.
    const customers = await prisma.customer.findMany({
      take: limit,
      orderBy: { customerId: "asc" },
      include: { _count: { select: { rentals: true } } },
    });
    return customers.map((c) => ({ customerId: c.customerId, firstName: c.firstName, rentals: c._count.rentals }));
  }
  // "query": a second SELECT ... WHERE customer_id IN (...), like selectinload.
  // "join": one SELECT with a LATERAL join, like joinedload (needs the relationJoins preview feature).
  const customers = await prisma.customer.findMany({
    take: limit,
    orderBy: { customerId: "asc" },
    relationLoadStrategy: strategy,
    include: { rentals: { select: { rentalId: true } } },
  });
  return customers.map((c) => ({ customerId: c.customerId, firstName: c.firstName, rentals: c.rentals.length }));
}

// GET /api/customers?limit=20&eager=false|true&strategy=query|join|count
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const limit = Math.min(Math.max(Number(params.get("limit") ?? 20) || 20, 1), 500);
  const isEager = params.get("eager") === "true";
  const strategy = (params.get("strategy") ?? "query") as Strategy;
  if (!["query", "join", "count"].includes(strategy)) {
    return NextResponse.json({ error: "strategy must be query, join or count" }, { status: 400 });
  }

  const started = performance.now();
  const { result, sql } = await countQueries(() => (isEager ? eager(limit, strategy) : lazy(limit)));
  return NextResponse.json({
    eager: isEager,
    strategy: isEager ? strategy : null,
    queries: sql.length,
    ms: Math.round(performance.now() - started),
    customers: result,
  });
}
