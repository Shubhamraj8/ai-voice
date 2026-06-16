DROP FUNCTION IF EXISTS public.retrieve_knowledge(uuid, vector, float, int);

DROP POLICY IF EXISTS tenant_isolation ON knowledge_embeddings;
DROP POLICY IF EXISTS internal_full_access ON knowledge_embeddings;
ALTER TABLE knowledge_embeddings DISABLE ROW LEVEL SECURITY;
