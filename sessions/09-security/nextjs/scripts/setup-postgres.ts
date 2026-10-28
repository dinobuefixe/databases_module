import "dotenv/config";
import { Client } from "pg";

// Creates the three roles from the tutorial (if they do not exist yet) and
// grants them least-privilege access to this project's database.
// Runs as the superuser (ADMIN_DATABASE_URL); the application never uses it.
//
// Roles belong to the whole PostgreSQL server, not to one database, and other
// projects share them. So this script never drops a role and never changes an
// existing password: the password from .env is only used when creating a role.
const ROLES = [
  ["migrations", "MIGRATIONS_PASSWORD"],
  ["app", "APP_PASSWORD"],
  ["readonly", "READONLY_PASSWORD"],
] as const;

async function main() {
  const admin = new Client({ connectionString: process.env.ADMIN_DATABASE_URL });
  await admin.connect();
  try {
    for (const [role, envVar] of ROLES) {
      const password = process.env[envVar];
      if (!password) throw new Error(`${envVar} is not set`);
      // DO blocks take no parameters, so the password goes through a session
      // setting (set_config is parameterised) and format(%L) quotes it.
      await admin.query("SELECT set_config('setup.password', $1, false)", [password]);
      await admin.query(`
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${role}') THEN
            EXECUTE format('CREATE ROLE ${role} LOGIN PASSWORD %L', current_setting('setup.password'));
            RAISE NOTICE 'created role ${role}';
          END IF;
        END
        $$`);
    }
    await admin.query("SELECT set_config('setup.password', '', false)");

    // Grants on this database only. Every statement can be run again safely.
    await admin.query(`
      DO $$
      BEGIN
        EXECUTE format('ALTER DATABASE %I OWNER TO migrations', current_database());
      END
      $$`);
    await admin.query(`
      REVOKE CREATE ON SCHEMA public FROM PUBLIC;
      -- Pagila's public schema belongs to postgres, so migrations needs CREATE explicitly.
      GRANT CREATE, USAGE ON SCHEMA public TO migrations;
      GRANT USAGE ON SCHEMA public TO app, readonly;

      GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app;
      GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app;
      GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

      -- Tables that migrations creates later get the same grants automatically.
      ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
          GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app;
      ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
          GRANT USAGE ON SEQUENCES TO app;
      ALTER DEFAULT PRIVILEGES FOR ROLE migrations IN SCHEMA public
          GRANT SELECT ON TABLES TO readonly;
    `);

    const { rows } = await admin.query(`
      SELECT r.rolname AS role, r.rolcanlogin AS login,
             has_table_privilege(r.rolname, 'public.film', 'SELECT') AS select_film,
             has_table_privilege(r.rolname, 'public.film', 'INSERT') AS insert_film,
             has_schema_privilege(r.rolname, 'public', 'CREATE') AS create_in_public
      FROM pg_roles r
      WHERE r.rolname IN ('migrations', 'app', 'readonly')
      ORDER BY r.rolname`);
    console.table(rows);
    console.log(`Database ${admin.database} is now owned by migrations.`);
  } finally {
    await admin.end();
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exitCode = 1;
});
