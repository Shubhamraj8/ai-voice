CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,
  business_name text NOT NULL,
  market text NOT NULL DEFAULT 'india_english',
  language text NOT NULL DEFAULT 'en',
  timezone text NOT NULL DEFAULT 'Asia/Kolkata',
  plan text NOT NULL DEFAULT 'starter',
  provider_config jsonb NOT NULL DEFAULT '{"stt":"cartesia","tts":"inworld","llm":"deepseek_native"}'::jsonb,
  onboarding_mode text NOT NULL DEFAULT 'self_serve',
  archived_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT tenants_market_check CHECK (
    market IN ('india_english', 'india_hindi', 'us_english', 'us_hipaa', 'global_english')
  ),
  CONSTRAINT tenants_onboarding_mode_check CHECK (
    onboarding_mode IN ('sales_led', 'self_serve', 'hybrid')
  )
);

CREATE INDEX tenants_slug_idx ON tenants (slug);
CREATE INDEX tenants_active_idx ON tenants (id) WHERE archived_at IS NULL;
