DROP POLICY IF EXISTS internal_full_access ON audit_log;
DROP POLICY IF EXISTS tenant_isolation ON audit_log;
ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON call_messages;
DROP POLICY IF EXISTS tenant_isolation ON call_messages;
ALTER TABLE call_messages DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON calls;
DROP POLICY IF EXISTS tenant_isolation ON calls;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON agents;
DROP POLICY IF EXISTS tenant_isolation ON agents;
ALTER TABLE agents DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON internal_users;
DROP POLICY IF EXISTS internal_user_self ON internal_users;
ALTER TABLE internal_users DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON tenant_users;
DROP POLICY IF EXISTS tenant_isolation ON tenant_users;
ALTER TABLE tenant_users DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS internal_full_access ON tenants;
DROP POLICY IF EXISTS tenant_isolation ON tenants;
ALTER TABLE tenants DISABLE ROW LEVEL SECURITY;

DROP FUNCTION IF EXISTS public.current_tenant_id();
DROP FUNCTION IF EXISTS public.is_internal_user();
DROP FUNCTION IF EXISTS public.user_tenant_ids();
