import { NextResponse } from "next/server";
import { parseId, readAmount } from "@/lib/amount";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@/generated/prisma/client";

export const dynamic = "force-dynamic";

// POST /api/customers/{id}/top-up {"amount": 50}: adds to the balance so the charge can be tried.
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const amount = await readAmount(request);
  if (typeof amount === "string") return NextResponse.json({ error: amount }, { status: 422 });

  try {
    // increment becomes "SET balance = balance + $1": atomic, no read first, no lock needed.
    const customer = await prisma.customer.update({
      where: { customer_id: id },
      data: { balance: { increment: amount } },
      select: { customer_id: true, balance: true },
    });
    return NextResponse.json(customer);
  } catch (err) {
    // P2025: the row to update does not exist.
    if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2025") {
      return NextResponse.json({ error: "Customer not found" }, { status: 404 });
    }
    throw err;
  }
}
