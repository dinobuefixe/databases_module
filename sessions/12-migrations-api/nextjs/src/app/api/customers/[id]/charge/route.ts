import { NextResponse } from "next/server";
import { parseId, readAmount } from "@/lib/amount";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@/generated/prisma/client";

export const dynamic = "force-dynamic";

class HttpError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

// POST /api/customers/{id}/charge {"amount": 10.50}
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const id = parseId((await params).id);
  if (id === null) return NextResponse.json({ error: "Invalid customer id" }, { status: 400 });
  const amount = await readAmount(request);
  if (typeof amount === "string") return NextResponse.json({ error: amount }, { status: 422 });

  try {
    // Interactive transaction: commits when the callback returns, rolls back if it throws.
    const balance = await prisma.$transaction(async (tx) => {
      // Prisma has no with_for_update(), so the lock is taken with raw SQL in the same transaction.
      // Another charge for this customer waits here until we commit.
      const rows = await tx.$queryRaw<{ balance: Prisma.Decimal }[]>`
        SELECT balance FROM customer WHERE customer_id = ${id} FOR UPDATE`;
      if (rows.length === 0) throw new HttpError(404, "Customer not found");
      if (rows[0].balance.lt(amount)) throw new HttpError(409, "Insufficient balance");

      const updated = await tx.customer.update({
        where: { customer_id: id },
        data: { balance: rows[0].balance.minus(amount) },
        select: { balance: true },
      });
      return updated.balance;
    });
    return NextResponse.json({ customer_id: id, balance });
  } catch (err) {
    if (err instanceof HttpError) return NextResponse.json({ error: err.message }, { status: err.status });
    throw err;
  }
}
