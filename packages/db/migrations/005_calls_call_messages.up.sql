CREATE TABLE calls (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE RESTRICT,
  twilio_call_sid text UNIQUE NOT NULL,
  from_number text NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz,
  duration_secs int,
  recording_url text,
  summary text,
  outcome text,
  cost_usd numeric(10, 5),
  provider_snapshot jsonb,
  CONSTRAINT calls_outcome_check CHECK (
    outcome IS NULL OR outcome IN ('booked', 'transferred', 'info_only', 'abandoned')
  )
);

CREATE INDEX calls_tenant_id_idx ON calls (tenant_id);
CREATE INDEX calls_agent_id_idx ON calls (agent_id);
CREATE INDEX calls_started_at_idx ON calls (started_at DESC);

CREATE TABLE call_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  call_id uuid NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  role text NOT NULL,
  content text NOT NULL,
  tool_name text,
  tool_args jsonb,
  tool_result jsonb,
  latency_ms int,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT call_messages_role_check CHECK (
    role IN ('user', 'assistant', 'tool', 'system')
  )
);

CREATE INDEX call_messages_call_id_idx ON call_messages (call_id);
CREATE INDEX call_messages_tenant_id_idx ON call_messages (tenant_id);
