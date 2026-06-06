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

Expected output: migrations `001` through `007` show as **applied**.

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

All seven migrations should be **applied**. If you re-run `migrate:up`, it should print `No pending migrations.`

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
| `006_rls_policies` | RLS + `current_tenant_id()` |
| `007_signup_creates_tenant` | `handle_new_user()` trigger on `auth.users` |

## Signup tenant provisioning (ticket 1.09)

After migration `007`, every new row in `auth.users` (email signup or admin-created user) automatically:

1. Creates one `tenants` row (`market = india_english`, `language = en`, India English `provider_config`)
2. Links the user in `tenant_users` with role `owner`

The trigger is idempotent: if `tenant_users` already exists for that `user_id`, no second tenant is created.

Verify:

```bash
pnpm migrate:up
pnpm --filter @ai-voice/db run test:signup-tenant
```

Manual check: sign up at `/signup`, then confirm in Supabase **Table Editor** → `tenants` + `tenant_users` (no manual SQL seed needed for portal access).

## Row Level Security (ticket 1.04)

Migration `006_rls_policies` enables RLS on all tenant-scoped tables plus membership tables.

### Helpers

- `user_tenant_ids()` — `SECURITY DEFINER` set of tenant IDs for `auth.uid()` (used in policies to avoid RLS recursion).
- `is_internal_user()` — `SECURITY DEFINER` boolean for internal admin membership.
- `current_tenant_id()` — first `tenant_users.tenant_id` for `auth.uid()` (convenience for app code).

### Policy pattern

Each data table has two policies for the `authenticated` role:

| Policy | Who | Rule |
|--------|-----|------|
| `tenant_isolation` | Tenant users | Row `tenant_id` in `user_tenant_ids()` (or tenant id in that set for `tenants`) |
| `internal_full_access` | Internal admins | `is_internal_user()` |

`tenant_users` uses `user_id = auth.uid()` (avoids self-referential recursion). `internal_users` combines self-read and internal full-access policies.

`audit_log` tenant policy additionally requires `tenant_id IS NOT NULL` so tenant users do not see global audit rows.

### Re-apply safely

Policies use `DROP POLICY IF EXISTS` before `CREATE POLICY`, so `migrate:up` is idempotent for `006`.

## Cross-tenant RLS test (ticket 1.05)

Verifies tenant A cannot read or mutate tenant B data via the Supabase API (real JWT + RLS).

### Prerequisites

- `.env` at repo root with `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- Migration `006` applied: `pnpm migrate:up`
- Python 3.11+ with pip

### Run locally

```bash
python -m pip install -r packages/db/requirements-test.txt
pnpm test:rls
```

The suite seeds two tenants, runs SELECT / INSERT / UPDATE / DELETE checks, and cleans up. It should finish in under 10 seconds.

### CI

Workflow job `db-rls` runs on every PR when these GitHub Actions secrets are set:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

If secrets are missing, the job is skipped with a notice (web/api jobs still run).

## Internal users (ticket 3.01)

Internal staff are stored in `internal_users` with roles `admin`, `sales`, or `support`.

### Founding internal user (auto-promote)

Set on the **API** service (Render / `apps/api/.env`):

```bash
INTERNAL_USER_EMAIL=you@yourcompany.com
```

When that email signs up via the normal Supabase auth flow and signs in at `/internal/login`, the API promotes them to `admin` on the first authenticated internal request. No public API can self-promote arbitrary emails — only an exact match to `INTERNAL_USER_EMAIL`.

### Add another internal user manually (SQL)

Run in the Supabase SQL editor after the person has signed up (so they exist in `auth.users`):

```sql
-- Replace with the user's auth UUID and desired role.
INSERT INTO internal_users (user_id, role)
VALUES ('00000000-0000-0000-0000-000000000000', 'support')
ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role;
```

To find `user_id` by email:

```sql
SELECT id, email FROM auth.users WHERE email = 'colleague@yourcompany.com';
```

## Troubleshooting

- **`password authentication failed`** — wrong password in `DATABASE_URL`
- **`connection timed out`** — use **Direct** connection string, not pooler, for migrations
- **`permission denied to create extension`** — run migrations as the `postgres` user via the dashboard connection string (default on new projects)
- **`relation auth.users does not exist`** — you are not connected to a Supabase database (Auth schema missing)
