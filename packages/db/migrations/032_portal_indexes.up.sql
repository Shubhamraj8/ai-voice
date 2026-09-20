CREATE INDEX IF NOT EXISTS calls_tenant_started_at_idx ON calls (tenant_id, started_at DESC);
CREATE INDEX IF NOT EXISTS calls_tenant_outcome_idx ON calls (tenant_id, outcome);
CREATE INDEX IF NOT EXISTS calls_tenant_intent_idx ON calls (tenant_id, intent);
CREATE INDEX IF NOT EXISTS knowledge_documents_tenant_uploaded_idx ON knowledge_documents (tenant_id, uploaded_at DESC);
