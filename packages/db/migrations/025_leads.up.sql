-- Ticket 5.02 — sales leads from landing-page CTAs (v1 sales-led onboarding).
-- Leads are global (pre-tenant), so no tenant_id / tenant RLS — internal staff
-- only. The public POST /leads writes via the service role (bypasses RLS).

CREATE TABLE leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_name text,
  contact_name text,
  contact_email text NOT NULL,
  contact_phone text,
  message text,
  source text,
  status text NOT NULL DEFAULT 'new',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT leads_status_check CHECK (
    status IN ('new', 'contacted', 'converted', 'lost')
  )
);

CREATE INDEX leads_status_idx ON leads (status);
CREATE INDEX leads_created_at_idx ON leads (created_at DESC);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON leads;
CREATE POLICY internal_full_access ON leads
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
