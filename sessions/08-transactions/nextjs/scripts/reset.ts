import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { resetAccounts } from "@/lib/withdraw";

// npm run reset -- [balance]    accounts 1 and 2 back to 100 (or the given balance)
async function main() {
  const rows = await resetAccounts(Number(process.argv[2] ?? 100));
  console.table(rows.map((r) => ({ id: r.id, balance: r.balance.toString() })));
}

main().finally(() => prisma.$disconnect());
