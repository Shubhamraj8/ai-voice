-- Ticket 4.09 — SMS audit log for the sendSms tool.

CREATE TABLE sms_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  call_id uuid REFERENCES calls(id) ON DELETE SET NULL,
  to_number text NOT NULL,
  body text NOT NULL,
  twilio_sid text,
  status text NOT NULL DEFAULT 'queued',
  error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX sms_log_tenant_id_idx ON sms_log (tenant_id);
-- Status webhook backfills by Twilio MessageSid.
CREATE INDEX sms_log_twilio_sid_idx ON sms_log (twilio_sid);

-- Same tenant-isolation RLS pattern as migration 006.
ALTER TABLE sms_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON sms_log;
CREATE POLICY tenant_isolation ON sms_log
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON sms_log;
CREATE POLICY internal_full_access ON sms_log
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
