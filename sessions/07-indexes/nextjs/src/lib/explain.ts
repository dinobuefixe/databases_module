import { Prisma } from "@/generated/prisma/client";
import { prisma } from "@/lib/prisma";

// The tutorial's queries, as Prisma.sql fragments so the same text can be
// shown and wrapped in EXPLAIN. Values stay parameters ($1).
export const queries = {
  // Composite index (customer_id, rented_at DESC) matches the filter and the sort.
  "customer-latest": (p: URLSearchParams) =>
    Prisma.sql`SELECT * FROM big_rental WHERE customer_id = ${Number(p.get("customer") ?? 42)} ORDER BY rented_at DESC LIMIT 10`,
  // Partial index on rented_at WHERE returned_at IS NULL: about 3% of the rows.
  "open-rentals": () =>
    Prisma.sql`SELECT count(*) FROM big_rental WHERE returned_at IS NULL AND rented_at < now() - interval '30 days'`,
  // Expression index on lower(email): the WHERE must use the same expression.
  "customer-email": (p: URLSearchParams) =>
    Prisma.sql`SELECT customer_id, first_name, last_name FROM customer WHERE lower(email) = lower(${p.get("email") ?? "MARY.SMITH@sakilacustomer.org"})`,
  // Plain index on rented_at: used when few rows match (days=7), not when most do (730).
  "recent-rentals": (p: URLSearchParams) =>
    Prisma.sql`SELECT * FROM big_rental WHERE rented_at > now() - make_interval(days => ${Number(p.get("days") ?? 730)}::int)`,
};

export type QueryName = keyof typeof queries;

export async function explain(name: QueryName, params = new URLSearchParams()) {
  const query = queries[name](params);
  // ?force_index=1 turns off sequential and bitmap scans for this query only,
  // to time the index scan the planner rejected. SET LOCAL ends with the transaction.
  const forceIndex = params.get("force_index") === "1";
  const rows = await prisma.$transaction(async (tx) => {
    if (forceIndex) {
      await tx.$executeRaw`SET LOCAL enable_seqscan = off`;
      await tx.$executeRaw`SET LOCAL enable_bitmapscan = off`;
    }
    // EXPLAIN (ANALYZE, BUFFERS) runs the query and returns the plan, one line per row.
    return tx.$queryRaw<{ "QUERY PLAN": string }[]>`EXPLAIN (ANALYZE, BUFFERS) ${query}`;
  });
  const plan = rows.map((r) => r["QUERY PLAN"]);
  const time = (label: string) => Number(plan.find((l) => l.startsWith(label))?.match(/([\d.]+) ms/)?.[1]);
  return {
    query: query.text,
    values: query.values,
    forceIndex,
    planningMs: time("Planning Time"),
    executionMs: time("Execution Time"),
    // Which scans did the planner pick? "Seq Scan" means no index was used.
    scans: plan.map((l) => l.match(/(Seq Scan|Index Only Scan|Index Scan|Bitmap Index Scan|Bitmap Heap Scan)( using \S+)? on \S+/)?.[0])
      .filter(Boolean),
    plan,
  };
}

// Indexes on the two tables, with their size on disk.
export function listIndexes() {
  return prisma.$queryRaw<{ table: string; index: string; size: string; definition: string }[]>`
    SELECT tablename AS table, indexname AS index,
           pg_size_pretty(pg_relation_size(format('%I', indexname)::regclass)) AS size,
           indexdef AS definition
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename IN ('big_rental', 'customer')
    ORDER BY tablename, indexname`;
}
