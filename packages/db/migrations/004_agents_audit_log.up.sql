CREATE TABLE agents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name text NOT NULL,
  starter_prompt text NOT NULL,
  system_prompt text NOT NULL,
  tools text[] NOT NULL DEFAULT '{}',
  voice_id text NOT NULL,
  phone_number text UNIQUE NOT NULL,
  twilio_sid text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  version int NOT NULL DEFAULT 1,
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agents_starter_prompt_check CHECK (
    starter_prompt IN ('receptionist', 'restaurant', 'hotel', 'retail', 'generic_support')
  )
);

CREATE INDEX agents_tenant_id_idx ON agents (tenant_id);
CREATE INDEX agents_phone_number_idx ON agents (phone_number);

CREATE TABLE audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  actor_type text NOT NULL,
  tenant_id uuid REFERENCES tenants(id) ON DELETE SET NULL,
  action text NOT NULL,
  payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT audit_log_actor_type_check CHECK (
    actor_type IN ('tenant_user', 'internal_user', 'system')
  )
);

CREATE INDEX audit_log_tenant_id_idx ON audit_log (tenant_id);
CREATE INDEX audit_log_created_at_idx ON audit_log (created_at DESC);
