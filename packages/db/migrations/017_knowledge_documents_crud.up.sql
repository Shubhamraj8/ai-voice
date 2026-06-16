-- Ticket 4.02 — CRUD support for knowledge_documents.
-- Soft delete (keep the row for audit, purge embeddings + storage separately)
-- and an ingestion-progress target (chunk_count).

ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS deleted_at timestamptz;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS chunk_count int;

-- Dedup must only consider live documents, so the same file can be re-uploaded
-- after a delete. Replace the plain unique constraint with a partial index.
ALTER TABLE knowledge_documents
  DROP CONSTRAINT IF EXISTS knowledge_documents_tenant_sha_unique;

CREATE UNIQUE INDEX IF NOT EXISTS knowledge_documents_tenant_sha_active_uidx
  ON knowledge_documents (tenant_id, sha256)
  WHERE deleted_at IS NULL;
