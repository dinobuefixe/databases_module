import "dotenv/config";
import { isDeepStrictEqual } from "node:util";
import { prisma } from "@/lib/prisma";
import { questions } from "@/lib/questions";

// Run both versions of each question and check they return the same rows.
// JSON round trip so that decimals compare by value, as the API returns them.
const asJson = (rows: unknown) => JSON.parse(JSON.stringify(rows));

async function main() {
  let failed = false;
  for (const [name, q] of Object.entries(questions)) {
    const [orm, sql] = [asJson(await q.orm()), asJson(await q.sql())];
    const same = isDeepStrictEqual(orm, sql);
    failed ||= !same;
    console.log(`${same ? "same " : "DIFF "} ${name.padEnd(26)} orm ${orm.length} rows, sql ${sql.length} rows`);
    if (!same) console.log("  first orm row:", orm[0], "\n  first sql row:", sql[0]);
  }
  process.exitCode = failed ? 1 : 0;
}

main().finally(() => prisma.$disconnect());
