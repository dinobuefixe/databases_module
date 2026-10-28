import { NextResponse } from "next/server";
import { parseId } from "@/lib/params";
import { prisma } from "@/lib/prisma";
import { profileKey } from "@/lib/profile";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

// PUT /api/admin/customers/{id}/profile {"first_name": "...", "last_name": "...", "email": "..."}
export async function PUT(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const body = await request.json().catch(() => null);
  const { first_name, last_name, email } = body ?? {};
  if (typeof first_name !== "string" || typeof last_name !== "string") {
    return NextResponse.json({ error: "first_name and last_name are required" }, { status: 400 });
  }

  const exists = await prisma.customer.count({ where: { customer_id: id } });
  if (!exists) return NextResponse.json({ error: "Customer not found" }, { status: 404 });

  const profile = await prisma.customer.update({
    where: { customer_id: id },
    data: { first_name, last_name, email: typeof email === "string" ? email : undefined, last_update: new Date() },
    select: { customer_id: true, first_name: true, last_name: true, email: true },
  });

  const redis = await getRedis();
  await redis.set(profileKey(id), JSON.stringify(profile));

  return NextResponse.json(profile);
}
