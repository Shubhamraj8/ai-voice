-- Helpers (SECURITY DEFINER avoids RLS recursion in policy subqueries)
CREATE OR REPLACE FUNCTION public.user_tenant_ids()
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid();
$$;

CREATE OR REPLACE FUNCTION public.is_internal_user()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM internal_users WHERE user_id = auth.uid()
  );
$$;

CREATE OR REPLACE FUNCTION public.current_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = public
AS $$
  SELECT tenant_id
  FROM tenant_users
  WHERE user_id = auth.uid()
  ORDER BY created_at
  LIMIT 1;
$$;

GRANT EXECUTE ON FUNCTION public.user_tenant_ids() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_internal_user() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_tenant_id() TO authenticated;

-- tenants
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON tenants;
CREATE POLICY tenant_isolation ON tenants
  FOR ALL
  TO authenticated
  USING (id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON tenants;
CREATE POLICY internal_full_access ON tenants
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- tenant_users
ALTER TABLE tenant_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON tenant_users;
CREATE POLICY tenant_isolation ON tenant_users
  FOR ALL
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS internal_full_access ON tenant_users;
CREATE POLICY internal_full_access ON tenant_users
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- internal_users
ALTER TABLE internal_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_user_self ON internal_users;
CREATE POLICY internal_user_self ON internal_users
  FOR ALL
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS internal_full_access ON internal_users;
CREATE POLICY internal_full_access ON internal_users
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- agents
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON agents;
CREATE POLICY tenant_isolation ON agents
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON agents;
CREATE POLICY internal_full_access ON agents
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- calls
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON calls;
CREATE POLICY tenant_isolation ON calls
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON calls;
CREATE POLICY internal_full_access ON calls
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- call_messages
ALTER TABLE call_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON call_messages;
CREATE POLICY tenant_isolation ON call_messages
  FOR ALL
  TO authenticated
  USING (tenant_id IN (SELECT public.user_tenant_ids()))
  WITH CHECK (tenant_id IN (SELECT public.user_tenant_ids()));

DROP POLICY IF EXISTS internal_full_access ON call_messages;
CREATE POLICY internal_full_access ON call_messages
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());

-- audit_log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation ON audit_log;
CREATE POLICY tenant_isolation ON audit_log
  FOR ALL
  TO authenticated
  USING (
    tenant_id IS NOT NULL
    AND tenant_id IN (SELECT public.user_tenant_ids())
  )
  WITH CHECK (
    tenant_id IS NOT NULL
    AND tenant_id IN (SELECT public.user_tenant_ids())
  );

DROP POLICY IF EXISTS internal_full_access ON audit_log;
CREATE POLICY internal_full_access ON audit_log
  FOR ALL
  TO authenticated
  USING (public.is_internal_user())
  WITH CHECK (public.is_internal_user());
