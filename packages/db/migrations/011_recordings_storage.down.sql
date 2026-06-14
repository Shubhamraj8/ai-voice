DROP POLICY IF EXISTS "recordings_service_role_all" ON storage.objects;

-- Only removes the bucket row; objects must be cleared first if any exist.
DELETE FROM storage.buckets WHERE id = 'recordings';
