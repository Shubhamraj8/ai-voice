-- Ticket 2.14 — private Supabase Storage bucket for call recordings.
-- Recordings are written by the backend (service role) and read by end users
-- only through short-lived signed URLs; no anon/authenticated direct access.

INSERT INTO storage.buckets (id, name, public)
VALUES ('recordings', 'recordings', false)
ON CONFLICT (id) DO NOTHING;

-- Explicit service-role full access to objects in the recordings bucket.
-- (The service role bypasses RLS anyway; this documents the intended access
-- and keeps the policy set self-describing.) No policies are granted to anon
-- or authenticated, so the bucket stays private — signed URLs bypass RLS.
CREATE POLICY "recordings_service_role_all"
  ON storage.objects
  FOR ALL
  TO service_role
  USING (bucket_id = 'recordings')
  WITH CHECK (bucket_id = 'recordings');
