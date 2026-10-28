import { DB, assertOwnDatabase, psql } from "./shell";

// npm run simulate-disaster
// Deletes rows from three tables of THIS project's database, like a bad
// DELETE or a buggy migration would. Run npm run backup first.
async function main() {
  assertOwnDatabase(DB);
  const statements = [
    "DELETE FROM film_actor WHERE actor_id <= 50",
    "DELETE FROM film_category WHERE category_id IN (1, 2, 3)",
    "DELETE FROM payment WHERE payment_date >= '2022-03-01' AND payment_date < '2022-05-01'",
  ];
  for (const sql of statements) {
    const { stdout } = await psql(DB, sql);
    console.log(`${stdout.trim().padEnd(12)} ${sql}`);
  }
  console.log(`\nData lost in ${DB}. Recover it with npm run restore-table, then npm run verify.`);
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
