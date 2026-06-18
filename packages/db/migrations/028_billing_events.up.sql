-- Ticket 5.05 (table pulled forward from 5.07) — billing / usage ledger.
-- v1 has no payment gateway: payments are recorded manually (5.05) and usage is
-- rolled up daily (5.06) for the portal billing page + manual invoicing.

CREATE TABLE billing_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  call_id uuid REFERENCES calls(id) ON DELETE SET NULL,
  event_type text NOT NULL,
  units numeric(10, 4),       -- minutes, for usage rows
  amount_inr numeric(10, 2),  -- for payment rows
  metadata_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT billing_events_type_check CHECK (
    event_type IN ('payment_recorded', 'usage_reported', 'access_extended', 'plan_changed')
  )
);

CREATE INDEX billing_events_tenant_id_idx ON billing_events (tenant_id);
CREATE INDEX billing_events_created_at_idx ON billing_events (created_at DESC);

-- Same tenant-isolation RLS pattern as migration 006 (tenants read their own
-- billing events in the portal; internal staff read all).
ALTER TABLE billing_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON billing_events;
CREATE POLICY tenant_isolation ON billing_events
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON billing_events;
CREATE POLICY internal_full_access ON billing_events
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
