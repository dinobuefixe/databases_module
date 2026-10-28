import "dotenv/config";
import { prisma } from "@/lib/prisma";
import { explain, queries, type QueryName } from "@/lib/explain";

// Print the plan of each tutorial query (or only the one named).
// Usage: npm run explain -- [customer-latest|open-rentals|customer-email|recent-rentals] [key=value ...]
// e.g.   npm run explain -- recent-rentals days=7
//        npm run explain -- recent-rentals force_index=1
async function main() {
  const only = process.argv[2] as QueryName | undefined;
  const names = only ? [only] : (Object.keys(queries) as QueryName[]);
  const params = new URLSearchParams(process.argv.slice(3).join("&"));
  for (const name of names) {
    const result = await explain(name, params);
    console.log(`\n=== ${name}: ${result.executionMs} ms (${result.scans.join(", ")})`);
    console.log(result.query, result.values);
    console.log(result.plan.join("\n"));
  }
}

main().finally(() => prisma.$disconnect());
