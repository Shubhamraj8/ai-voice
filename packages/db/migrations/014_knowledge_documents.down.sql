DROP POLICY IF EXISTS "knowledge_service_role_all" ON storage.objects;
DELETE FROM storage.buckets WHERE id = 'knowledge';
DROP TABLE IF EXISTS knowledge_documents;
