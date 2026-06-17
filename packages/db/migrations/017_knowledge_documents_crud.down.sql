DROP INDEX IF EXISTS knowledge_documents_tenant_sha_active_uidx;

ALTER TABLE knowledge_documents
  ADD CONSTRAINT knowledge_documents_tenant_sha_unique UNIQUE (tenant_id, sha256);

ALTER TABLE knowledge_documents DROP COLUMN IF EXISTS chunk_count;
ALTER TABLE knowledge_documents DROP COLUMN IF EXISTS deleted_at;
