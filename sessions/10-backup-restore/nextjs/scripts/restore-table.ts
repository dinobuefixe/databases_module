import path from "node:path";
import { DB, PG_USER, assertOwnDatabase, dumpFile, pg, psql, seconds } from "./shell";

// npm run restore-table -- [table] [dump]       (default table: film_actor)
// Restores one table's rows from a dump into the live database:
// empty the table, then load only its data.
//
// Why not pg_restore --clean -t film_actor? --clean drops and recreates the
// table, which fails because the views actor_info and film_list depend on it.
// And a partitioned table such as payment keeps its rows in the partitions
// (payment_p2022_01, ...): -t payment restores nothing, each partition has to
// be named with its own -t.
async function main() {
  const table = process.argv[2] ?? "film_actor";
  const dump = dumpFile(process.argv[3]);
  assertOwnDatabase(DB);
  if (!/^[a-z_][a-z0-9_]*$/.test(table)) throw new Error(`Not a plain table name: ${table}`);

  // TRUNCATE on a partitioned table empties every partition, and -t on it
  // restores nothing: refuse, and name the partitions instead.
  const kind = (await psql(DB, `SELECT relkind FROM pg_class WHERE oid = '${table}'::regclass`)).stdout.trim();
  if (kind === "p") {
    const parts = (await psql(DB, `SELECT string_agg(inhrelid::regclass::text, ' ' ORDER BY 1) FROM pg_inherits WHERE inhparent = '${table}'::regclass`)).stdout.trim();
    throw new Error(`${table} is partitioned; restore its partitions one by one instead:\n  ${parts}`);
  }

  const before = (await psql(DB, `SELECT count(*) FROM ${table}`)).stdout.trim();
  const start = performance.now();
  await psql(DB, `TRUNCATE ${table}`);
  // --single-transaction: if the load fails, nothing is half loaded.
  await pg(["pg_restore", "-U", PG_USER, "-d", DB, "--data-only", "--single-transaction", "-t", table], {
    stdinFile: dump,
  });
  const after = (await psql(DB, `SELECT count(*) FROM ${table}`)).stdout.trim();
  console.log(`${table}: ${before} rows before, ${after} rows after, from ${path.basename(dump)} in ${seconds(start)} s`);
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
