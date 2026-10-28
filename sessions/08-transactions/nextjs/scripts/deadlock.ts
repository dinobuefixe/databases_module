import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { resetAccounts } from "@/lib/withdraw";

// Two transfers at the same time: A moves 10 from account 1 to 2, B moves 10
// from 2 to 1. Each locks its source row first, waits a moment, then locks its
// destination: A holds 1 and waits for 2, B holds 2 and waits for 1. PostgreSQL
// detects the cycle after about a second (deadlock_timeout) and aborts one.
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function transfer(name: string, from: number, to: number, orderedLocks: boolean) {
  // The fix: always lock rows in the same order (ascending id), whatever the
  // direction of the transfer.
  const [first, second] = orderedLocks ? [Math.min(from, to), Math.max(from, to)] : [from, to];
  try {
    await prisma.$transaction(
      async (tx) => {
        await tx.$queryRaw`SELECT id FROM account WHERE id = ${first} FOR UPDATE`;
        console.log(`  ${name}: locked account ${first}`);
        await sleep(200);
        console.log(`  ${name}: waiting for account ${second}`);
        await tx.$queryRaw`SELECT id FROM account WHERE id = ${second} FOR UPDATE`;
        await tx.account.update({ where: { id: from }, data: { balance: { decrement: 10 } } });
        await tx.account.update({ where: { id: to }, data: { balance: { increment: 10 } } });
      },
      { timeout: 10_000 },
    );
    console.log(`  ${name}: committed`);
  } catch (err) {
    // The PostgreSQL error is kept in meta.driverAdapterError.cause.
    const cause = (err as { meta?: { driverAdapterError?: { cause?: { originalCode?: string; originalMessage?: string } } } })
      .meta?.driverAdapterError?.cause;
    if (cause?.originalCode !== "40P01") throw err;
    console.log(`  ${name}: ABORTED, SQLSTATE 40P01: ${cause.originalMessage}`);
    console.log(`  ${name}: the application should retry this transaction`);
  }
}

async function run(orderedLocks: boolean) {
  await resetAccounts(100);
  await Promise.all([transfer("A (1 -> 2)", 1, 2, orderedLocks), transfer("B (2 -> 1)", 2, 1, orderedLocks)]);
  const accounts = await prisma.account.findMany({ orderBy: { id: "asc" } });
  console.log(`  balances: ${accounts.map((a) => `${a.id}=${a.balance}`).join(", ")}\n`);
}

async function main() {
  console.log("Locks in opposite order:");
  await run(false);
  console.log("Locks in ascending id order:");
  await run(true);
}

main().finally(() => prisma.$disconnect());
