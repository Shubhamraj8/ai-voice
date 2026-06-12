-- Removes the seeded dev agent + tenant. Calls referencing them block the
-- delete (agent FK is ON DELETE RESTRICT); clear dev calls first if needed.
DELETE FROM agents WHERE id = '00000000-0000-0000-0000-000000000002';
DELETE FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';
