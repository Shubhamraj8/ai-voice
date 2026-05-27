# @ai-voice/db

Postgres migrations for the AI Voice platform (Supabase).

## What you do manually (Supabase Dashboard)

These steps cannot be done from this repo alone.

### 1. Organization (you already did this)

- You created a Supabase organization. No further org setup is required for 1.03.

### 2. Create the project

1. Open [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. **New project**
3. Settings:
   - **Name**: e.g. `ai-voice-dev`
   - **Database password**: generate a strong password and save it in your password manager
   - **Region**: **Asia Pacific (Mumbai) — ap-south-1** (required by `design.md`)
4. Wait until the project status is **Active** (a few minutes)

### 3. Copy credentials into `.env`

From the project dashboard:

| Value | Where to find it |
|-------|------------------|
| `SUPABASE_URL` | **Project Settings → API → Project URL** |
| `SUPABASE_ANON_KEY` | **Project Settings → API → anon public** |
| `SUPABASE_SERVICE_ROLE_KEY` | **Project Settings → API → service_role** (keep secret) |
| `DATABASE_URL` | **Project Settings → Database → Connection string → URI** |

Steps for `DATABASE_URL`:

1. Go to **Project Settings → Database**
2. Under **Connection string**, choose **URI**
3. Pick **Direct connection** (host `db.<ref>.supabase.co`, port **5432**)
4. Replace `[YOUR-PASSWORD]` with your database password
5. Paste into `.env` at the repo root:

```bash
cp .env.example .env
# edit .env with your real values
```

Never commit `.env`. It is already gitignored.

### 4. (Optional) Invite teammates

**Organization Settings → Members** — add teammates who need dashboard access.

### 5. Run migrations from your machine

From the repository root:

```bash
pnpm install
pnpm --filter @ai-voice/db run migrate:status
pnpm --filter @ai-voice/db run migrate:up
```

Expected output: migrations `001` through `005` show as **applied**.

### 6. Verify in Supabase

**Table Editor** — confirm tables exist:

- `tenants`
- `tenant_users`
- `internal_users`
- `agents`
- `audit_log`
- `calls`
- `call_messages`
- `schema_migrations`

**Database → Extensions** — confirm:

- `vector` (pgvector)
- `uuid-ossp`

**SQL Editor** (optional):

```sql
SELECT extname FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');
```

### 7. Schema drift check (acceptance criteria)

After `migrate:up`, compare local migration state with the remote DB:

```bash
pnpm --filter @ai-voice/db run migrate:status
```

All five migrations should be **applied**. If you re-run `migrate:up`, it should print `No pending migrations.`

To test rollback and re-apply:

```bash
pnpm --filter @ai-voice/db run migrate:down   # rolls back one migration
pnpm --filter @ai-voice/db run migrate:up     # re-applies it
```

Or full reset (destroys all tables created by these migrations):

```bash
pnpm --filter @ai-voice/db run migrate:reset
```

## Migrations included (ticket 1.03)

| Version | Description |
|---------|-------------|
| `001_extensions` | `uuid-ossp`, `vector` |
| `002_tenants` | `tenants` |
| `003_tenant_users_internal_users` | `tenant_users`, `internal_users` |
| `004_agents_audit_log` | `agents`, `audit_log` |
| `005_calls_call_messages` | `calls`, `call_messages` |

RLS policies are **not** part of 1.03 (later tickets).

## Troubleshooting

- **`password authentication failed`** — wrong password in `DATABASE_URL`
- **`connection timed out`** — use **Direct** connection string, not pooler, for migrations
- **`permission denied to create extension`** — run migrations as the `postgres` user via the dashboard connection string (default on new projects)
- **`relation auth.users does not exist`** — you are not connected to a Supabase database (Auth schema missing)
