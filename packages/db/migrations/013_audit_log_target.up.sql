-- Ticket 3.11 — structured audit targets. Records which entity an action
-- affected (e.g. target_type='agent', target_id=<agent uuid>) so the audit
-- trail is queryable per entity, not just per tenant.
ALTER TABLE audit_log ADD COLUMN target_type text;
ALTER TABLE audit_log ADD COLUMN target_id uuid;

CREATE INDEX audit_log_target_idx ON audit_log (target_type, target_id);
