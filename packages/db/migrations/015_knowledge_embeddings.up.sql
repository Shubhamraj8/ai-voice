-- Ticket 4.04/4.05 — vector store for RAG chunks. pgvector ('vector' type) is
-- enabled in migration 001. The retrieval SQL function + RLS land in 4.05.

CREATE TABLE knowledge_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_id uuid NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  chunk_index int NOT NULL,
  content text NOT NULL,
  token_count int,
  embedding vector(1536) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Filter by tenant before the vector scan (isolation + selectivity).
CREATE INDEX knowledge_embeddings_tenant_id_idx
  ON knowledge_embeddings (tenant_id);

-- Approximate-nearest-neighbour index for cosine similarity (the retrieval
-- function uses the <=> cosine-distance operator). lists=100 is a good default
-- under ~1M rows; rebuild with a higher value after large ingests (see README).
CREATE INDEX knowledge_embeddings_embedding_idx
  ON knowledge_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
