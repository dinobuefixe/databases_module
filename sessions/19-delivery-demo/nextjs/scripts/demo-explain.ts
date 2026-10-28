// Demo 3: EXPLAIN (ANALYZE, BUFFERS) before and after each index from session 07, on big_rental.
import "dotenv/config";
import { Prisma } from "@/generated/prisma/client";
import { prisma } from "@/lib/prisma";

// Constant SQL written in this file; no user input reaches Prisma.raw.
const cases = [
  {
    name: "composite index: one customer's latest rentals",
    query: "SELECT * FROM big_rental WHERE customer_id = 42 ORDER BY rented_at DESC LIMIT 10",
    index: "big_rental_customer_rented",
    create: "CREATE INDEX big_rental_customer_rented ON big_rental (customer_id, rented_at DESC)",
  },
  {
    name: "partial index: rentals not returned after 30 days",
    query: "SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days'",
    index: "big_rental_open",
    create: "CREATE INDEX big_rental_open ON big_rental (rented_at) WHERE returned_at IS NULL",
  },
];

async function explain(query: string) {
  const rows = await prisma.$queryRaw<{ "QUERY PLAN": string }[]>`EXPLAIN (ANALYZE, BUFFERS) ${Prisma.raw(query)}`;
  const plan = rows.map((r) => r["QUERY PLAN"]);
  return {
    plan,
    node: plan.find((l) => /Scan/.test(l))?.trim().replace(/\s+\(cost.*$/, "").replace(/^->\s*/, "") ?? plan[0],
    ms: Number(/Execution Time: ([\d.]+)/.exec(plan.join("\n"))?.[1]),
    buffers: /Buffers: (.*)/.exec(plan.join("\n"))?.[1] ?? "",
  };
}

async function main() {
  const summary = [];
  for (const c of cases) {
    await prisma.$executeRaw`DROP INDEX IF EXISTS ${Prisma.raw(c.index)}`;
    const before = await explain(c.query);
    await prisma.$executeRaw`${Prisma.raw(c.create)}`;
    const after = await explain(c.query);

    console.log(`\n=== ${c.name}\n${c.query}\n\n--- before\n${before.plan.join("\n")}\n\n${c.create};\n\n--- after\n${after.plan.join("\n")}`);
    summary.push({ case: c.index, "before ms": before.ms, "after ms": after.ms, "plan before": before.node, "plan after": after.node });
  }
  console.log("\nSummary");
  console.table(summary);
}

main().finally(() => prisma.$disconnect());
