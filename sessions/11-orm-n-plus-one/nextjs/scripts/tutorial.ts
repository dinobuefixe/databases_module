// The session 11 tutorial as a script: N+1, the fix, and an aggregation.
// Run with LOG_SQL=true (the default in .env.example) to see every statement.
import "dotenv/config";
import { countQueries, prisma } from "@/lib/prisma";

async function main() {
  // N+1: one query for 20 customers, then one query per customer.
  const nPlusOne = await countQueries(async () => {
    const customers = await prisma.customer.findMany({ take: 20, orderBy: { customerId: "asc" } });
    for (const c of customers) {
      const rentals = await prisma.rental.findMany({ where: { customerId: c.customerId } });
      console.log(c.firstName, rentals.length);
    }
  });

  // Fixed: include loads every customer's rentals in a second query (WHERE customer_id IN (...)).
  const fixed = await countQueries(async () => {
    const customers = await prisma.customer.findMany({
      take: 20,
      orderBy: { customerId: "asc" },
      relationLoadStrategy: "query",
      include: { rentals: true },
    });
    for (const c of customers) console.log(c.firstName, c.rentals.length);
  });

  // Aggregation: top 5 customers by number of rentals, grouped in the database.
  const aggregation = await countQueries(async () => {
    const top = await prisma.rental.groupBy({
      by: ["customerId"],
      _count: { rentalId: true },
      orderBy: { _count: { rentalId: "desc" } },
      take: 5,
    });
    for (const row of top) console.log(row.customerId, row._count.rentalId);
  });

  console.log("\nQueries per block:");
  console.log(`  N+1:         ${nPlusOne.sql.length}`);
  console.log(`  include:     ${fixed.sql.length}`);
  console.log(`  aggregation: ${aggregation.sql.length}`);
}

main().finally(() => prisma.$disconnect());
