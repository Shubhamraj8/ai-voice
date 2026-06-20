-- Ticket 5.13 — DPDP data deletion (right to erasure).
-- Soft-delete the tenant (keep the row so the audit trail survives) and track
-- email-confirmed deletion requests.

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
-- Internal safeguard: blocks accidental deletion of a protected (e.g. active
-- paying) tenant until staff explicitly clears the flag.
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS deletion_blocked boolean NOT NULL DEFAULT false;

CREATE TABLE dpdp_deletion_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  token_hash text NOT NULL,
  requested_by uuid,
  recipient_email text,
  status text NOT NULL DEFAULT 'pending',
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  confirmed_at timestamptz,
  completed_at timestamptz,
  CONSTRAINT dpdp_deletion_status_check CHECK (
    status IN ('pending', 'confirmed', 'completed')
  )
);

CREATE INDEX dpdp_deletion_requests_token_hash_idx
  ON dpdp_deletion_requests (token_hash);
CREATE INDEX dpdp_deletion_requests_tenant_id_idx
  ON dpdp_deletion_requests (tenant_id);

-- Same tenant-isolation RLS pattern as migration 006/028.
ALTER TABLE dpdp_deletion_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON dpdp_deletion_requests;
CREATE POLICY tenant_isolation ON dpdp_deletion_requests
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON dpdp_deletion_requests;
CREATE POLICY internal_full_access ON dpdp_deletion_requests
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
