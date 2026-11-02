// Withdrawals from session 08. Rule: the balance never goes below 0 and no withdrawal is lost.
import { prisma } from "@/lib/prisma";
import { Prisma } from "@/generated/prisma/client";

// Read, compute, write: two statements with a gap between them. Two requests can read the
// same balance and both write balance - amount: a lost update.
export async function withdrawNaive(id: number, amount: number) {
  const rows = await prisma.$queryRaw<{ balance: Prisma.Decimal }[]>`SELECT balance FROM account WHERE id = ${id}`;
  if (rows.length === 0 || rows[0].balance.lt(amount)) return false;
  await prisma.$executeRaw`UPDATE account SET balance = ${rows[0].balance.minus(amount)} WHERE id = ${id}`;
  return true;
}

// One conditional UPDATE: the check and the write happen in the same statement.
export async function withdrawAtomic(id: number, amount: number) {
  const { count } = await prisma.account.updateMany({
    where: { id, balance: { gte: amount } },
    data: { balance: { decrement: amount } },
  });
  return count === 1;
}
