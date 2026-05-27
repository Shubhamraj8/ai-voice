CREATE TABLE tenant_users (
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, user_id),
  CONSTRAINT tenant_users_role_check CHECK (role IN ('owner', 'admin', 'member'))
);

CREATE INDEX tenant_users_user_id_idx ON tenant_users (user_id);

CREATE TABLE internal_users (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role text NOT NULL,
  added_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT internal_users_role_check CHECK (role IN ('admin', 'sales', 'support'))
);
