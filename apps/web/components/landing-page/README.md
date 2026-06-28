# Landing page module

All marketing landing page UI and SEO for ticket **1.14** live in this folder (ZERQO design handoff).

To redesign the landing page later, edit files here only — the route at `app/(marketing)/page.tsx` is a thin wrapper.

## Structure

| File                 | Purpose                                     |
| -------------------- | ------------------------------------------- |
| `landing-page.tsx`   | Composes all sections + Lenis smooth scroll |
| `nav-hero.tsx`       | Navigation, hero, marquee                   |
| `mid.tsx`            | Value prop, stats, how it works             |
| `verticals-dark.tsx` | Verticals + dark showcase                   |
| `pricing-faq.tsx`    | Pricing, testimonials, FAQ                  |
| `cta-footer.tsx`     | CTA banner, footer, scroll progress         |
| `lib.tsx`            | Shared motion/UI helpers                    |
| `index.css`          | Scoped styles (`.landing-page-root`)        |
| `routes.ts`          | `/login` path (app sign-in)                 |
| `seo.ts`             | Page metadata                               |

## CTAs

The "Sign in" button routes to `/login`. "Get started" opens the lead-capture dialog — onboarding is sales-led, so there is no public self-serve signup.
