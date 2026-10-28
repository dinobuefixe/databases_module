import { statSync } from "node:fs";
import path from "node:path";
import { BACKUP_DIR, DB, PG_USER, ensureBackupDir, pg, seconds } from "./shell";

// npm run backup
// pg_dump -Fc (custom format: compressed, restorable table by table) and
// pg_dumpall --roles-only (pg_dump does not include roles).
async function main() {
  ensureBackupDir();
  // Timestamp in UTC, e.g. 2026-10-07_143844.
  const stamp = new Date().toISOString().slice(0, 19).replace("T", "_").replace(/:/g, "");
  const dump = path.join(BACKUP_DIR, `${DB}_${stamp}.dump`);
  const roles = path.join(BACKUP_DIR, `roles_${stamp}.sql`);

  const start = performance.now();
  // -T in `exec -T` (added by pg()) keeps binary output intact.
  await pg(["pg_dump", "-U", PG_USER, "-Fc", DB], { stdoutFile: dump });
  console.log(`${path.relative(process.cwd(), dump)}  ${(statSync(dump).size / 1e6).toFixed(1)} MB in ${seconds(start)} s`);

  await pg(["pg_dumpall", "-U", PG_USER, "--roles-only"], { stdoutFile: roles });
  console.log(`${path.relative(process.cwd(), roles)}  ${statSync(roles).size} bytes`);
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
