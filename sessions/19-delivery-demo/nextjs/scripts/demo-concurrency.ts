// Demo 1: 50 simultaneous withdrawals of 10 from a balance of 100.
// The rule holds when exactly 10 succeed and the balance ends at 0.
import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { withdrawAtomic, withdrawNaive } from "@/lib/withdraw";

const REQUESTS = 50;
const AMOUNT = 10;

async function attempt(name: string, withdraw: (id: number, amount: number) => Promise<boolean>) {
  await prisma.account.update({ where: { id: 1 }, data: { balance: 100 } });
  const results = await Promise.all(Array.from({ length: REQUESTS }, () => withdraw(1, AMOUNT)));
  const succeeded = results.filter(Boolean).length;
  const { balance } = await prisma.account.findUniqueOrThrow({ where: { id: 1 } });
  // Every success took 10, so the balance should be 100 - 10 * successes.
  const holds = succeeded === 10 && balance.eq(0);
  console.log(
    `${name.padEnd(8)} ${String(succeeded).padStart(3)} of ${REQUESTS} succeeded, final balance ${balance
      .toString()
      .padStart(4)}, money handed out ${succeeded * AMOUNT}  ${holds ? "RULE HOLDS" : "RULE BROKEN"}`,
  );
  return holds;
}

async function main() {
  console.log(`Account 1 starts at 100. ${REQUESTS} concurrent withdrawals of ${AMOUNT}.\n`);
  await attempt("naive", withdrawNaive); // before: read, then write
  const ok = await attempt("atomic", withdrawAtomic); // after: one conditional UPDATE
  process.exitCode = ok ? 0 : 1;
}

main().finally(() => prisma.$disconnect());
