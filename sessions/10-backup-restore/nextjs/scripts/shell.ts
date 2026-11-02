import "dotenv/config";
import { spawn } from "node:child_process";
import { closeSync, existsSync, mkdirSync, openSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

// Helpers shared by the backup scripts. The PostgreSQL tools run inside the
// postgres container through `docker compose exec -T`, exactly as in the
// tutorial, so you do not need pg_dump installed on your machine.

export const PROJECT_DIR = path.resolve(__dirname, "..");
export const REPO_ROOT = process.env.REPO_ROOT ?? path.resolve(PROJECT_DIR, "../../..");
export const BACKUP_DIR = path.join(PROJECT_DIR, "backups");

const url = new URL(process.env.DATABASE_URL!);
export const PG_USER = decodeURIComponent(url.username);
export const DB = url.pathname.slice(1);
export const RESTORE_DB = process.env.RESTORE_DB ?? `${DB}_restored`;

// A connection string for another database on the same server.
export function urlFor(database: string): string {
  const other = new URL(process.env.DATABASE_URL!);
  other.pathname = `/${database}`;
  return other.toString();
}

type RunOptions = { stdinFile?: string; stdoutFile?: string; allowFailure?: boolean };

// Run a command. stdin can come from a file and stdout can go to a file, like
// `< backup.dump` and `> backup.dump` in the shell.
export function run(cmd: string, args: string[], opts: RunOptions = {}) {
  return new Promise<{ code: number; stdout: string; stderr: string }>((resolve, reject) => {
    const stdin = opts.stdinFile ? openSync(opts.stdinFile, "r") : "ignore";
    const stdout = opts.stdoutFile ? openSync(opts.stdoutFile, "w") : "pipe";
    const child = spawn(cmd, args, { cwd: REPO_ROOT, stdio: [stdin, stdout, "pipe"] });
    let out = "";
    let err = "";
    child.stdout?.on("data", (d) => (out += d));
    child.stderr?.on("data", (d) => (err += d));
    child.on("error", reject);
    child.on("close", (code) => {
      if (typeof stdin === "number") closeSync(stdin);
      if (typeof stdout === "number") closeSync(stdout);
      const result = { code: code ?? 1, stdout: out, stderr: err };
      if (result.code !== 0 && !opts.allowFailure) {
        reject(new Error(`${cmd} ${args.join(" ")} exited with ${result.code}\n${err}`));
      } else {
        resolve(result);
      }
    });
  });
}

// docker compose exec -T postgres <args>, from the repository root.
export function pg(args: string[], opts: RunOptions = {}) {
  return run("docker", ["compose", "exec", "-T", "postgres", ...args], opts);
}

export function psql(database: string, sql: string, opts: RunOptions = {}) {
  return pg(["psql", "-U", PG_USER, "-d", database, "-v", "ON_ERROR_STOP=1", "-tA", "-c", sql], opts);
}

// The newest dump of this project's database, or the one given as an argument.
export function dumpFile(arg?: string): string {
  if (arg) return path.resolve(arg);
  const dumps = existsSync(BACKUP_DIR)
    ? readdirSync(BACKUP_DIR)
        .filter((f) => f.startsWith(`${DB}_`) && f.endsWith(".dump"))
        .map((f) => path.join(BACKUP_DIR, f))
        .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs)
    : [];
  if (dumps.length === 0) throw new Error("No dump found in backups/. Run npm run backup first.");
  return dumps[0];
}

export function ensureBackupDir() {
  mkdirSync(BACKUP_DIR, { recursive: true });
}

export function seconds(start: number) {
  return ((performance.now() - start) / 1000).toFixed(2);
}

// The scripts that change data refuse to touch any database that is not this project's.
export function assertOwnDatabase(database: string) {
  if (!database.startsWith("s10_nextjs")) {
    throw new Error(`Refusing to touch ${database}: only databases starting with s10_nextjs belong to this project`);
  }
}
