-- Ticket 5.01 — pricing plans config (no payment gateway in v1).
-- Backend source of truth for plan limits/prices: used by the marketing pricing
-- page, manual invoicing, payment recording (5.05), and usage overage (5.06).

CREATE TABLE pricing_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key text UNIQUE NOT NULL,
  name text NOT NULL,
  price_inr_month int NOT NULL,
  included_minutes int NOT NULL,
  overage_inr_per_min numeric(10, 2) NOT NULL,
  phone_numbers int NOT NULL DEFAULT 1,
  active boolean NOT NULL DEFAULT true,
  sort_order int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Seed matches the live landing page (Starter / Growth / Pro).
INSERT INTO pricing_plans
  (key, name, price_inr_month, included_minutes, overage_inr_per_min, phone_numbers, sort_order)
VALUES
  ('starter', 'Starter', 2999, 300, 15, 1, 1),
  ('growth', 'Growth', 6999, 800, 13, 1, 2),
  ('pro', 'Pro', 16999, 2000, 12, 2, 3)
ON CONFLICT (key) DO NOTHING;
