import "dotenv/config";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { Client } from "pg";
import { from as copyFrom } from "pg-copy-streams";
import { fakerEN_GB as faker } from "@faker-js/faker";
import { prisma } from "@/lib/prisma";

// Load the same N person rows three ways and compare the time:
//   1. COPY (one command that streams every row)
//   2. one INSERT per row
//   3. Prisma createMany (multi-row INSERTs)
// Usage: npm run bulk:person -- [rows]      (default 100000)
const rows = Number(process.argv[2] ?? 100_000);

type Person = { name: string; email: string; city: string };

// Faker with a fixed seed: every run produces the same people.
function generate(n: number): Person[] {
  faker.seed(42);
  return Array.from({ length: n }, () => ({
    name: faker.person.fullName(),
    email: faker.internet.email(),
    city: faker.location.city(),
  }));
}

// COPY's text format: tab-separated columns, one row per line.
// Backslash, tab and newline must be escaped.
const escape = (v: string) => v.replace(/\\/g, "\\\\").replace(/\t/g, "\\t").replace(/\n/g, "\\n");

async function timed(label: string, run: () => Promise<void>) {
  await prisma.$executeRaw`TRUNCATE person RESTART IDENTITY`;
  const start = performance.now();
  await run();
  const seconds = (performance.now() - start) / 1000;
  const [{ count }] = await prisma.$queryRaw<{ count: bigint }[]>`SELECT count(*) FROM person`;
  console.log(`${label.padEnd(24)} ${seconds.toFixed(2).padStart(7)} s   ${count} rows   ${Math.round(rows / seconds)} rows/s`);
}

async function main() {
  console.log(`Generating ${rows} people with Faker (seed 42)...`);
  const people = generate(rows);

  // Prisma has no COPY, so we use the pg driver (which Prisma's adapter uses
  // underneath) with pg-copy-streams.
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();

  await timed("COPY", async () => {
    const stream = client.query(copyFrom("COPY person (name, email, city) FROM STDIN"));
    const lines = Readable.from(people.map((p) => `${escape(p.name)}\t${escape(p.email)}\t${escape(p.city)}\n`));
    await pipeline(lines, stream);
  });

  await timed("INSERT per row", async () => {
    for (const p of people) {
      await client.query("INSERT INTO person (name, email, city) VALUES ($1, $2, $3)", [p.name, p.email, p.city]);
    }
  });

  await timed("Prisma createMany", async () => {
    await prisma.person.createMany({ data: people });
  });

  await client.end();
}

main().finally(() => prisma.$disconnect());
