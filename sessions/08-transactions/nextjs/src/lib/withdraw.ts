import { prisma } from "@/lib/prisma";

export type Strategy = "naive" | "atomic" | "lock";
export type Result = { ok: true; balance: string } | { ok: false; reason: "not_found" | "insufficient_funds" };

// Naive: read, compute in the application, write. Two requests can read the
// same balance and both write their result: the second overwrites the first
// (lost update). This is the code the tutorial asks you to break.
async function naive(id: number, amount: number): Promise<Result> {
  const account = await prisma.account.findUnique({ where: { id } });
  if (!account) return { ok: false, reason: "not_found" };
  if (account.balance.lessThan(amount)) return { ok: false, reason: "insufficient_funds" };
  const updated = await prisma.account.update({
    where: { id },
    data: { balance: account.balance.minus(amount) },
  });
  return { ok: true, balance: updated.balance.toString() };
}

// Fix 1, atomic conditional update:
// UPDATE account SET balance = balance - 10 WHERE id = 1 AND balance >= 10
// Read and write happen in one statement; count says whether it applied.
async function atomic(id: number, amount: number): Promise<Result> {
  const { count } = await prisma.account.updateMany({
    where: { id, balance: { gte: amount } },
    data: { balance: { decrement: amount } },
  });
  if (count === 0) {
    const exists = await prisma.account.count({ where: { id } });
    return { ok: false, reason: exists ? "insufficient_funds" : "not_found" };
  }
  const account = await prisma.account.findUniqueOrThrow({ where: { id } });
  return { ok: true, balance: account.balance.toString() };
}

// Fix 2, row lock: SELECT ... FOR UPDATE inside a transaction. Other
// transactions that want the same row wait until this one commits, then read
// the new balance.
async function lock(id: number, amount: number): Promise<Result> {
  return prisma.$transaction(
    async (tx) => {
      const rows = await tx.$queryRaw<{ balance: string }[]>`
        SELECT balance::text FROM account WHERE id = ${id} FOR UPDATE`;
      if (rows.length === 0) return { ok: false, reason: "not_found" } as const;
      if (Number(rows[0].balance) < amount) return { ok: false, reason: "insufficient_funds" } as const;
      const updated = await tx.account.update({
        where: { id },
        data: { balance: { decrement: amount } },
      });
      return { ok: true, balance: updated.balance.toString() } as const;
    },
    // Many requests queue for the same row and for a pooled connection, so
    // allow more than the default 2 s to start and 5 s to finish.
    { maxWait: 15_000, timeout: 15_000 },
  );
}

export const strategies: Record<Strategy, (id: number, amount: number) => Promise<Result>> = { naive, atomic, lock };

// Accounts 1 and 2 back to a known balance.
export async function resetAccounts(balance = 100) {
  await prisma.$transaction([
    prisma.account.upsert({ where: { id: 1 }, create: { id: 1, balance }, update: { balance } }),
    prisma.account.upsert({ where: { id: 2 }, create: { id: 2, balance }, update: { balance } }),
  ]);
  return prisma.account.findMany({ orderBy: { id: "asc" } });
}
