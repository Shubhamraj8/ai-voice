-- Restore the ungated handle_new_user (always auto-creates a tenant on signup).
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  new_tenant_id uuid;
  base_slug text;
  final_slug text;
  display_name text;
  india_provider_config jsonb := '{"stt":"cartesia","tts":"inworld","llm":"deepseek_native"}'::jsonb;
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.tenant_users WHERE user_id = NEW.id
  ) THEN
    RETURN NEW;
  END IF;

  base_slug := lower(
    regexp_replace(split_part(coalesce(NEW.email, 'user'), '@', 1), '[^a-z0-9]+', '-', 'g')
  );
  base_slug := trim(both '-' from coalesce(nullif(base_slug, ''), 'tenant'));
  final_slug := base_slug || '-' || substr(replace(NEW.id::text, '-', ''), 1, 8);

  WHILE EXISTS (SELECT 1 FROM public.tenants WHERE slug = final_slug) LOOP
    final_slug := base_slug || '-' || substr(replace(gen_random_uuid()::text, '-', ''), 1, 8);
  END LOOP;

  display_name := coalesce(
    nullif(trim(NEW.raw_user_meta_data->>'business_name'), ''),
    nullif(trim(split_part(coalesce(NEW.email, ''), '@', 1)), ''),
    'My Business'
  );

  INSERT INTO public.tenants (
    slug, business_name, market, language, timezone, plan,
    provider_config, onboarding_mode
  ) VALUES (
    final_slug, display_name, 'india_english', 'en', 'Asia/Kolkata', 'starter',
    india_provider_config, 'self_serve'
  )
  RETURNING id INTO new_tenant_id;

  INSERT INTO public.tenant_users (tenant_id, user_id, role)
  VALUES (new_tenant_id, NEW.id, 'owner');

  RETURN NEW;
END;
$$;
