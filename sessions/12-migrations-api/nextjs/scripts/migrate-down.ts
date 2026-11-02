// Reverts the last applied migration, like `alembic downgrade -1`.
// Prisma Migrate only goes forward, so each migration we want to revert has a hand-written down.sql.
import "dotenv/config";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { Client } from "pg";

async function main() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  await client.connect();
  try {
    // Prisma records every applied migration in _prisma_migrations.
    const { rows } = await client.query<{ id: string; migration_name: string }>(`
      SELECT id, migration_name FROM _prisma_migrations
      WHERE finished_at IS NOT NULL AND rolled_back_at IS NULL
      ORDER BY finished_at DESC, migration_name DESC
      LIMIT 1`);
    if (rows.length === 0) throw new Error("No applied migrations");
    const { id, migration_name: name } = rows[0];

    const downFile = join("prisma", "migrations", name, "down.sql");
    if (!existsSync(downFile)) throw new Error(`${name} has no down.sql, so it cannot be reverted`);

    // DDL is transactional in PostgreSQL: the down script and the bookkeeping succeed or fail together.
    await client.query("BEGIN");
    await client.query(readFileSync(downFile, "utf8"));
    // Marked as rolled back, so `prisma migrate deploy` applies it again.
    await client.query("UPDATE _prisma_migrations SET rolled_back_at = now() WHERE id = $1", [id]);
    await client.query("COMMIT");
    console.log(`Reverted ${name}`);
  } catch (err) {
    await client.query("ROLLBACK").catch(() => {});
    console.error((err as Error).message);
    process.exitCode = 1;
  } finally {
    await client.end();
  }
}

main();
