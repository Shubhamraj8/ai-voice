-- Ticket 4.01 — knowledge documents (uploaded PDFs) + private storage bucket.

CREATE TABLE knowledge_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  agent_id uuid REFERENCES agents(id) ON DELETE SET NULL,
  filename text NOT NULL,
  storage_path text NOT NULL,
  bytes int NOT NULL,
  sha256 text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  error text,
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  CONSTRAINT knowledge_documents_status_check CHECK (
    status IN ('pending', 'processing', 'ready', 'error')
  ),
  -- Same file content can't be uploaded twice for one tenant (dedup).
  CONSTRAINT knowledge_documents_tenant_sha_unique UNIQUE (tenant_id, sha256)
);

CREATE INDEX knowledge_documents_tenant_id_idx ON knowledge_documents (tenant_id);

-- Private bucket; backend (service role) writes, end users read via signed URLs.
INSERT INTO storage.buckets (id, name, public)
VALUES ('knowledge', 'knowledge', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "knowledge_service_role_all"
  ON storage.objects
  FOR ALL
  TO service_role
  USING (bucket_id = 'knowledge')
  WITH CHECK (bucket_id = 'knowledge');
