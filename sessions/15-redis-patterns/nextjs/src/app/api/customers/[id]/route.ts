import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

type Params = { params: Promise<{ id: string }> };
const TTL_SECONDS = 300;
const cacheKey = (id: number) => `cache:customer:${id}`;

function loadCustomer(id: number) {
  return prisma.customer.findUnique({
    where: { customer_id: id },
    select: { customer_id: true, first_name: true, last_name: true, email: true },
  });
}

// GET /api/customers/{id}: cache-aside. Redis first; on a miss, PostgreSQL, then store with a TTL.
export async function GET(_request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const redis = await getRedis();

  const cached = await redis.get(cacheKey(id));
  if (cached !== null) {
    return NextResponse.json({ cache: "hit", ttl: await redis.ttl(cacheKey(id)), customer: JSON.parse(cached) });
  }

  const customer = await loadCustomer(id);
  if (!customer) return NextResponse.json({ error: "Customer not found" }, { status: 404 });
  await redis.set(cacheKey(id), JSON.stringify(customer), { expiration: { type: "EX", value: TTL_SECONDS } });
  return NextResponse.json({ cache: "miss", ttl: TTL_SECONDS, customer });
}

// PATCH /api/customers/{id} {"first_name": "...", "last_name": "...", "email": "..."}
// Writes PostgreSQL (the source of truth) first, then deletes the cache key.
export async function PATCH(request: Request, { params }: Params) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const body = await request.json().catch(() => null);

  const changes: { first_name?: string; last_name?: string; email?: string } = {};
  for (const field of ["first_name", "last_name", "email"] as const) {
    if (typeof body?.[field] === "string" && body[field].trim()) changes[field] = body[field].trim();
  }
  if (Object.keys(changes).length === 0) {
    return NextResponse.json({ error: "Send at least one of first_name, last_name, email" }, { status: 400 });
  }

  const { count } = await prisma.customer.updateMany({
    where: { customer_id: id },
    data: { ...changes, last_update: new Date() },
  });
  if (count === 0) return NextResponse.json({ error: "Customer not found" }, { status: 404 });

  // Delete rather than overwrite: the next GET reloads the row as PostgreSQL has it.
  const deleted = await (await getRedis()).del(cacheKey(id));
  return NextResponse.json({ updated: changes, cacheKeyDeleted: deleted === 1 });
}
