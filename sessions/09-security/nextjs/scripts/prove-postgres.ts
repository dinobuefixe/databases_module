import "dotenv/config";
import { Client } from "pg";

// The tutorial's permission tests, each run while connected as the role
// itself. Every statement runs inside BEGIN ... ROLLBACK, so even if a grant
// were wrong, nothing would be changed.
type Check = { role: string; url: string; label: string; sql: string; shouldFail: boolean };

const app = process.env.DATABASE_URL!;
const readonly = process.env.READONLY_DATABASE_URL!;

const checks: Check[] = [
  { role: "app", url: app, label: "SELECT from customer", sql: "SELECT count(*) FROM customer", shouldFail: false },
  { role: "app", url: app, label: "INSERT into actor", sql: "INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')", shouldFail: false },
  { role: "app", url: app, label: "DROP TABLE film", sql: "DROP TABLE film", shouldFail: true },
  { role: "app", url: app, label: "CREATE TABLE", sql: "CREATE TABLE app_was_here (id int)", shouldFail: true },
  { role: "readonly", url: readonly, label: "SELECT from actor", sql: "SELECT count(*) FROM actor", shouldFail: false },
  { role: "readonly", url: readonly, label: "INSERT into actor", sql: "INSERT INTO actor (first_name, last_name) VALUES ('X', 'Y')", shouldFail: true },
];

async function main() {
  let wrong = 0;
  for (const check of checks) {
    const client = new Client({ connectionString: check.url });
    await client.connect();
    let error: string | null = null;
    try {
      await client.query("BEGIN");
      await client.query(check.sql);
    } catch (err) {
      error = (err as Error).message;
    } finally {
      await client.query("ROLLBACK");
      await client.end();
    }
    const asExpected = (error !== null) === check.shouldFail;
    if (!asExpected) wrong++;
    const outcome = error ? `refused: ${error}` : "allowed";
    console.log(`${asExpected ? "PASS" : "FAIL"}  ${check.role.padEnd(8)} ${check.label.padEnd(22)} ${outcome}`);
  }
  process.exitCode = wrong ? 1 : 0;
}

main();
