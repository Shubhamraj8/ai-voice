import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import postgres from "postgres";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../../..");
const migrationsDir = path.resolve(__dirname, "../migrations");

dotenv.config({ path: path.resolve(repoRoot, ".env") });

const databaseUrl = process.env.DATABASE_URL;

if (!databaseUrl) {
  console.error("DATABASE_URL is not set. Copy .env.example to .env and add your Supabase connection string.");
  process.exit(1);
}

const command = process.argv[2] ?? "status";

function loadMigrations() {
  const files = fs
    .readdirSync(migrationsDir)
    .filter((file) => file.endsWith(".up.sql"))
    .sort();

  return files.map((file) => {
    const version = file.replace(".up.sql", "");
    return {
      version,
      upPath: path.join(migrationsDir, file),
      downPath: path.join(migrationsDir, `${version}.down.sql`),
    };
  });
}

async function ensureMigrationsTable(sql) {
  await sql`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version text PRIMARY KEY,
      applied_at timestamptz NOT NULL DEFAULT now()
    )
  `;
}

async function getAppliedVersions(sql) {
  const rows = await sql`SELECT version FROM schema_migrations ORDER BY version`;
  return rows.map((row) => row.version);
}

async function runSqlFile(sql, filePath) {
  const contents = fs.readFileSync(filePath, "utf8");
  await sql.unsafe(contents);
}

async function migrateUp(sql) {
  const migrations = loadMigrations();
  const applied = new Set(await getAppliedVersions(sql));
  const pending = migrations.filter((migration) => !applied.has(migration.version));

  if (pending.length === 0) {
    console.log("No pending migrations.");
    return;
  }

  for (const migration of pending) {
    console.log(`Applying ${migration.version}...`);
    await sql.begin(async (tx) => {
      await runSqlFile(tx, migration.upPath);
      await tx`INSERT INTO schema_migrations (version) VALUES (${migration.version})`;
    });
    console.log(`Applied ${migration.version}`);
  }
}

async function migrateDown(sql) {
  const migrations = loadMigrations();
  const applied = await getAppliedVersions(sql);

  if (applied.length === 0) {
    console.log("No migrations to roll back.");
    return;
  }

  const lastVersion = applied[applied.length - 1];
  const migration = migrations.find((item) => item.version === lastVersion);

  if (!migration) {
    throw new Error(`Unknown applied migration version: ${lastVersion}`);
  }

  if (!fs.existsSync(migration.downPath)) {
    throw new Error(`Missing down migration: ${migration.downPath}`);
  }

  console.log(`Rolling back ${migration.version}...`);
  await sql.begin(async (tx) => {
    await runSqlFile(tx, migration.downPath);
    await tx`DELETE FROM schema_migrations WHERE version = ${migration.version}`;
  });
  console.log(`Rolled back ${migration.version}`);
}

async function migrateStatus(sql) {
  const migrations = loadMigrations();
  const applied = new Set(await getAppliedVersions(sql));

  for (const migration of migrations) {
    const state = applied.has(migration.version) ? "applied" : "pending";
    console.log(`${migration.version}: ${state}`);
  }
}

async function migrateReset(sql) {
  console.log("Resetting database schema...");
  let applied = await getAppliedVersions(sql);

  while (applied.length > 0) {
    await migrateDown(sql);
    applied = await getAppliedVersions(sql);
  }

  await migrateUp(sql);
  console.log("Reset complete.");
}

async function main() {
  const sql = postgres(databaseUrl, { max: 1 });

  try {
    await ensureMigrationsTable(sql);

    switch (command) {
      case "up":
        await migrateUp(sql);
        break;
      case "down":
        await migrateDown(sql);
        break;
      case "status":
        await migrateStatus(sql);
        break;
      case "reset":
        await migrateReset(sql);
        break;
      default:
        console.error(`Unknown command: ${command}`);
        console.error("Usage: node scripts/migrate.mjs [up|down|status|reset]");
        process.exit(1);
    }
  } finally {
    await sql.end();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
