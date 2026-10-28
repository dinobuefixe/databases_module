import { Client } from "pg";
import { DB, RESTORE_DB, urlFor } from "./shell";

// npm run verify -- [databaseA] [databaseB]
// Compares the row count of every table in two databases (default: the live
// database and the restored one). Exits with code 1 on any difference, so it
// can run in a script or a scheduled job.
async function countRows(database: string): Promise<Map<string, number>> {
  const client = new Client({ connectionString: urlFor(database) });
  await client.connect();
  try {
    // relkind 'r': ordinary tables, including each partition of payment.
    const { rows: tables } = await client.query<{ name: string }>(`
      SELECT c.relname AS name
      FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'public' AND c.relkind = 'r'
      ORDER BY 1`);
    const counts = new Map<string, number>();
    for (const { name } of tables) {
      // Table names come from the catalogue, quoted as identifiers.
      const { rows } = await client.query(`SELECT count(*)::int AS n FROM public.${client.escapeIdentifier(name)}`);
      counts.set(name, rows[0].n);
    }
    return counts;
  } finally {
    await client.end();
  }
}

async function main() {
  const [a, b] = [process.argv[2] ?? DB, process.argv[3] ?? RESTORE_DB];
  const [countsA, countsB] = await Promise.all([countRows(a), countRows(b)]);
  const names = [...new Set([...countsA.keys(), ...countsB.keys()])].sort();
  let mismatches = 0;
  for (const name of names) {
    const [x, y] = [countsA.get(name), countsB.get(name)];
    if (x !== y) {
      mismatches++;
      console.log(`MISMATCH  ${name.padEnd(22)} ${a}: ${x ?? "missing"}   ${b}: ${y ?? "missing"}`);
    }
  }
  console.log(`${names.length} tables compared between ${a} and ${b}: ${mismatches} mismatches`);
  process.exitCode = mismatches ? 1 : 0;
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 2;
});
