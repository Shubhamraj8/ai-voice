-- Ticket 2.13 — fixed dev tenant + agent so call-lifecycle rows have valid
-- tenant_id / agent_id foreign keys until real tenant lookup lands (3.09).
-- The application references these exact UUIDs (see app/services/calls.py).
INSERT INTO tenants (id, slug, business_name)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'dev-seed',
  'Dev Seed Tenant'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO agents (
  id, tenant_id, name, starter_prompt, system_prompt,
  voice_id, phone_number, twilio_sid
)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',
  'Dev Seed Agent',
  'receptionist',
  'You are a helpful receptionist for the dev seed tenant.',
  'aura-2-helena-en',
  '+10000000000',
  'DEVSEED'
)
ON CONFLICT (id) DO NOTHING;
