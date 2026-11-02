import { NextResponse } from "next/server";
import { parseId } from "@/lib/amount";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET /api/customers/{id}: the two columns added by the migrations.
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });

  const customer = await prisma.customer.findUnique({
    where: { customer_id: id },
    select: { customer_id: true, first_name: true, last_name: true, active: true, tier: true, balance: true },
  });
  if (!customer) return NextResponse.json({ error: "Customer not found" }, { status: 404 });
  return NextResponse.json(customer);
}
