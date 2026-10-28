import path from "node:path";
import { PG_USER, RESTORE_DB, assertOwnDatabase, dumpFile, pg, seconds } from "./shell";

// npm run restore -- [dump]
// Restores the newest dump (or the one given) into a new database,
// s10_nextjs_restored, and measures how long pg_restore takes.
async function main() {
  const dump = dumpFile(process.argv[2]);
  assertOwnDatabase(RESTORE_DB);
  console.log(`Restoring ${path.basename(dump)} into ${RESTORE_DB}`);

  await pg(["dropdb", "-U", PG_USER, "--if-exists", "--force", RESTORE_DB]);
  await pg(["createdb", "-U", PG_USER, RESTORE_DB]);

  const start = performance.now();
  // --no-owner: objects belong to the user running the restore.
  const result = await pg(["pg_restore", "-U", PG_USER, "-d", RESTORE_DB, "--no-owner"], {
    stdinFile: dump,
    allowFailure: true,
  });
  console.log(`pg_restore finished in ${seconds(start)} s (exit code ${result.code})`);
  // pg_restore keeps going after errors and reports them at the end.
  if (result.code !== 0) {
    console.log(result.stderr);
    process.exitCode = 1;
  }
  console.log(`Next: npm run verify (compares every table with the live database)`);
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
