-- Ticket 5.03 — time-bound access. A tenant's agents answer only while
-- now() < paid_until; an expiry job pauses lapsed tenants.
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS paid_until timestamptz;
