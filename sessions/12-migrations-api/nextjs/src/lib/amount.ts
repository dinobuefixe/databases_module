import { Prisma } from "@/generated/prisma/client";

// Validates {"amount": ...} like the tutorial's Pydantic model: Decimal, greater than 0.
// Returns the amount, or an error message for a 422 response.
export async function readAmount(request: Request): Promise<Prisma.Decimal | string> {
  const body = await request.json().catch(() => null);
  const raw = body?.amount;
  if (typeof raw !== "number" && typeof raw !== "string") return "amount is required";
  if (!/^\d+(\.\d{1,2})?$/.test(String(raw))) return "amount must be a number with at most 2 decimal places";
  const amount = new Prisma.Decimal(raw);
  if (amount.lte(0)) return "amount must be greater than 0";
  return amount;
}

export function parseId(id: string): number | null {
  return /^\d+$/.test(id) ? Number(id) : null;
}
