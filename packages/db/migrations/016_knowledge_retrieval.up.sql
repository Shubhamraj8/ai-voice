-- Ticket 4.05 — RLS on knowledge_embeddings + the top-K retrieval function.
-- Table + indexes were created in migration 015.

ALTER TABLE knowledge_embeddings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON knowledge_embeddings;
CREATE POLICY tenant_isolation ON knowledge_embeddings
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON knowledge_embeddings;
CREATE POLICY internal_full_access ON knowledge_embeddings
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- Top-K cosine-similarity retrieval for one tenant. similarity = 1 - distance;
-- only rows at or above the threshold are returned, most similar first.
CREATE OR REPLACE FUNCTION public.retrieve_knowledge(
  p_tenant_id uuid,
  p_query_embedding vector(1536),
  p_threshold float DEFAULT 0.7,
  p_limit int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  chunk_index int,
  content text,
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT e.id, e.document_id, e.chunk_index, e.content,
         1 - (e.embedding <=> p_query_embedding) AS similarity
  FROM knowledge_embeddings e
  WHERE e.tenant_id = p_tenant_id
    AND 1 - (e.embedding <=> p_query_embedding) >= p_threshold
  ORDER BY e.embedding <=> p_query_embedding
  LIMIT p_limit;
$$;

GRANT EXECUTE ON FUNCTION public.retrieve_knowledge(uuid, vector, float, int)
  TO authenticated;
