-- Ticket 4.10 — owner escalation contacts + escalation audit log.

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS escalation_email text;
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS escalation_sms text;

ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_escalation_sms_e164;
ALTER TABLE tenants ADD CONSTRAINT tenants_escalation_sms_e164 CHECK (
  escalation_sms IS NULL OR escalation_sms ~ '^\+[1-9]\d{1,14}$'
);

CREATE TABLE escalations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  call_id uuid REFERENCES calls(id) ON DELETE SET NULL,
  summary text NOT NULL,
  urgency text NOT NULL,
  email_sent boolean NOT NULL DEFAULT false,
  sms_sent boolean NOT NULL DEFAULT false,
  payload jsonb,
  error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT escalations_urgency_check CHECK (urgency IN ('low', 'medium', 'high'))
);

CREATE INDEX escalations_tenant_id_idx ON escalations (tenant_id);

-- Same tenant-isolation RLS pattern as migration 006.
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON escalations;
CREATE POLICY tenant_isolation ON escalations
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON escalations;
CREATE POLICY internal_full_access ON escalations
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
