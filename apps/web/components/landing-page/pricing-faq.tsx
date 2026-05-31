// @ts-nocheck
"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Eyebrow, Heading2, Stagger, SI, Icon, Star } from "./lib";
import { useMobile, wrapPad, SECTION_PY } from "./mid";
import { landingRoutes } from "./routes";

const useS4 = useState,
  useR4 = useRef;
const M4 = motion,
  AP4 = AnimatePresence;

/* ============================================================
   pricing-faq.jsx — Pricing, Testimonials, FAQ
   ============================================================ */

/* ---------- PRICING ---------- */
const PLANS = [
  {
    name: "Starter",
    tag: "For solo businesses",
    tagDark: false,
    monthly: "₹2,999",
    annual: "₹2,499",
    annualNote: "₹29,988/year · saves ₹6,000",
    sub: "300 minutes included/month · 1 phone number",
    feats: [
      ["AI voice receptionist (24/7)", true],
      ["Knowledge base — 1 PDF upload", true],
      ["Call logs + transcripts", true],
      ["Transfer to human", true],
      ["SMS confirmation sending", true],
      ["Post-call summary", true],
      ["Google Calendar booking (available in Growth)", false],
      ["Analytics dashboard", false],
      ["Prompt editing portal", false],
      ["Multiple phone numbers", false],
    ],
    cta: "Start 7-day free trial",
    featured: false,
  },
  {
    name: "Growth",
    tag: "Most Popular",
    monthly: "₹6,999",
    annual: "₹5,833",
    annualNote: "₹69,996/year · saves ₹14,004",
    sub: "800 minutes included/month · 1 phone number",
    feats: [
      ["Everything in Starter", true],
      ["Google Calendar integration", true],
      ["Book, reschedule & cancel appointments", true],
      ["Analytics dashboard", true],
      ["Prompt editing in client portal", true],
      ["Call recording + playback", true],
      ["URL scraping for knowledge base", true],
      ["Multiple PDF uploads (unlimited)", true],
      ["24h priority email support", true],
      ["SMS + WhatsApp notifications (v1.5)", true],
    ],
    cta: "Get started free",
    featured: true,
  },
  {
    name: "Pro",
    tag: "For growing teams",
    monthly: "₹16,999",
    annual: "₹13,999",
    annualNote: "₹1,67,988/year · saves ₹36,000",
    sub: "2,000 minutes/month · 2 phone numbers",
    feats: [
      ["Everything in Growth", true],
      ["Premium AI voice (OpenAI HD quality)", true],
      ["Smarter LLM model (reasoning mode)", true],
      ["Advanced analytics + sentiment", true],
      ["Team portal access (3 users)", true],
      ["Custom webhook integrations", true],
      ["WhatsApp Business integration", true],
      ["2 concurrent phone lines", true],
      ["Monthly strategy call (30 min)", true],
      ["Priority support (4h response)", true],
    ],
    cta: "Talk to our team",
    featured: false,
  },
];

function FeatRow({ text, included, featured }) {
  if (featured) {
    return (
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <span
          style={{
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: "#F04E00",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            marginTop: 1,
          }}
        >
          <Icon name="check" size={10} stroke="#fff" sw={3} />
        </span>
        <span style={{ fontSize: 13, color: "#1C1C1C" }}>{text}</span>
      </div>
    );
  }
  return (
    <div
      style={{ display: "flex", gap: 10, alignItems: "flex-start", opacity: included ? 1 : 0.85 }}
    >
      <Icon name="check" size={14} stroke={included ? "#111" : "#D8D3CE"} sw={2.2} />
      <span style={{ fontSize: 13, color: included ? "#1C1C1C" : "#A09890" }}>{text}</span>
    </div>
  );
}

function PriceBlock({ plan, annual }) {
  return (
    <div>
      <AP4 mode="wait">
        <M4.div
          key={annual ? "a" : "m"}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25 }}
        >
          <span
            className="display"
            style={{ fontSize: 48, fontWeight: 700, letterSpacing: "-0.04em", color: "#111" }}
          >
            {annual ? plan.annual : plan.monthly}
          </span>
          <span style={{ fontSize: 15, fontWeight: 400, color: "#A09890" }}>/month</span>
          {annual && (
            <div style={{ fontSize: 12, color: "#16A34A", marginTop: 4 }}>{plan.annualNote}</div>
          )}
        </M4.div>
      </AP4>
    </div>
  );
}

function PricingCard({ plan, annual }) {
  const router = useRouter();
  const f = plan.featured;
  const goSignup = () => router.push(landingRoutes.signup);
  return (
    <div
      style={{
        position: "relative",
        background: "#fff",
        borderRadius: 20,
        padding: 28,
        border: f ? "1.5px solid #F04E00" : "1px solid #E8E3DE",
        boxShadow: f ? "0 0 0 5px rgba(240,78,0,0.07), 0 12px 40px rgba(0,0,0,0.08)" : "none",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      {f && (
        <span
          style={{
            position: "absolute",
            top: -14,
            left: "50%",
            transform: "translateX(-50%)",
            background: "#F04E00",
            color: "#fff",
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            padding: "5px 16px",
            borderRadius: 100,
            whiteSpace: "nowrap",
          }}
        >
          Most Popular
        </span>
      )}
      {!f && (
        <span
          style={{
            alignSelf: "flex-start",
            background: "#F4F0EC",
            color: "#6B6560",
            fontSize: 11,
            padding: "4px 10px",
            borderRadius: 100,
          }}
        >
          {plan.tag}
        </span>
      )}
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          color: f ? "#F04E00" : "#A09890",
          marginTop: f ? 8 : 12,
        }}
      >
        {plan.name}
      </div>
      <div style={{ marginTop: 8 }}>
        <PriceBlock plan={plan} annual={annual} />
      </div>
      <div style={{ height: 1, background: "#E8E3DE", margin: "20px 0" }} />
      <div style={{ fontSize: 13, color: "#6B6560" }}>{plan.sub}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 16, flex: 1 }}>
        {plan.feats.map(([t, inc]) => (
          <FeatRow key={t} text={t} included={inc} featured={f} />
        ))}
      </div>
      <M4.button
        whileHover={f ? { scale: 1.02 } : {}}
        whileTap={f ? { scale: 0.97 } : {}}
        onClick={plan.cta === "Talk to our team" ? undefined : goSignup}
        onMouseEnter={(e) => {
          if (!f) {
            e.currentTarget.style.background = "#111";
            e.currentTarget.style.color = "#fff";
            e.currentTarget.style.borderColor = "#111";
          } else {
            e.currentTarget.style.background = "#D94200";
            e.currentTarget.style.boxShadow = "0 8px 24px rgba(240,78,0,0.35)";
          }
        }}
        onMouseLeave={(e) => {
          if (!f) {
            e.currentTarget.style.background = "#fff";
            e.currentTarget.style.color = "#111";
            e.currentTarget.style.borderColor = "#E8E3DE";
          } else {
            e.currentTarget.style.background = "#F04E00";
            e.currentTarget.style.boxShadow = "none";
          }
        }}
        style={{
          marginTop: 24,
          width: "100%",
          padding: "13px",
          borderRadius: 12,
          fontSize: 14,
          fontWeight: 600,
          cursor: "pointer",
          transition: "all 200ms",
          background: f ? "#F04E00" : "#fff",
          color: f ? "#fff" : "#111",
          border: f ? "none" : "1px solid #E8E3DE",
        }}
      >
        {plan.cta}
      </M4.button>
    </div>
  );
}

function Pricing() {
  const mobile = useMobile();
  const [annual, setAnnual] = useS4(false);
  const ordered = mobile ? PLANS : PLANS;
  return (
    <section
      id="pricing"
      style={{ background: "#F8F5F1", ...SECTION_PY, paddingBottom: "clamp(56px,7vw,84px)" }}
    >
      <div style={wrapPad(mobile)}>
        <div
          style={{
            textAlign: "center",
            maxWidth: 520,
            margin: "0 auto",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Eyebrow text="Pricing" />
          <Heading2 style={{ textAlign: "center" }}>
            Start free. Scale without <span className="hl">surprises</span>.
          </Heading2>
          <p style={{ fontSize: 18, lineHeight: 1.72, color: "#6B6560", marginTop: 20 }}>
            Every plan includes a 7-day free trial. No credit card. No setup fees. Cancel anytime.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            justifyContent: "center",
            margin: "32px auto",
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 500, color: annual ? "#A09890" : "#111" }}>
            Monthly
          </span>
          <button
            onClick={() => setAnnual(!annual)}
            style={{
              width: 44,
              height: 26,
              borderRadius: 100,
              background: annual ? "#F04E00" : "#111",
              border: "none",
              position: "relative",
              cursor: "pointer",
              padding: 0,
            }}
          >
            <M4.span
              layout
              transition={{ type: "spring", stiffness: 500, damping: 32 }}
              style={{
                position: "absolute",
                top: 3,
                left: annual ? 21 : 3,
                width: 20,
                height: 20,
                borderRadius: "50%",
                background: "#fff",
              }}
            />
          </button>
          <span
            style={{
              fontSize: 14,
              fontWeight: 500,
              color: annual ? "#111" : "#A09890",
              display: "inline-flex",
              alignItems: "center",
            }}
          >
            Annual{" "}
            <span
              style={{
                background: "#ECFDF5",
                color: "#16A34A",
                fontSize: 10,
                fontWeight: 700,
                padding: "2px 7px",
                borderRadius: 100,
                marginLeft: 6,
              }}
            >
              Save 17%
            </span>
          </span>
        </div>

        <Stagger
          style={{
            display: "grid",
            gridTemplateColumns: mobile ? "1fr" : "repeat(3,1fr)",
            gap: 20,
            marginTop: 28,
            alignItems: "stretch",
          }}
        >
          {ordered.map((p) => (
            <SI key={p.name} style={{ height: "100%", marginTop: !mobile && p.featured ? -6 : 0 }}>
              <PricingCard plan={p} annual={annual} />
            </SI>
          ))}
        </Stagger>

        <p style={{ fontSize: 13, color: "#A09890", textAlign: "center", marginTop: 28 }}>
          All plans include a 7-day free trial with full features. No credit card required. Cancel
          anytime from your dashboard.
        </p>
        <div
          style={{
            display: "flex",
            gap: 32,
            justifyContent: "center",
            marginTop: 24,
            flexWrap: "wrap",
          }}
        >
          {[
            ["lock", "Secure payments via Stripe"],
            ["building", "DPDP Act compliant"],
            ["shield", "99.9% uptime SLA (Pro)"],
          ].map(([ic, t]) => (
            <span
              key={t}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                fontSize: 12,
                color: "#A09890",
              }}
            >
              <Icon name={ic} size={14} stroke="#A09890" />
              {t}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---------- TESTIMONIALS ---------- */
const TESTIMONIALS = [
  {
    type: "Dental Clinic",
    quote:
      "Before this, we were missing 30% of our calls after 6 PM. Now the AI handles everything — booking, rescheduling, even answering which doctor handles which procedure. My receptionist now focuses on patients in the clinic, not the phone.",
    name: "Dr. Priya Mehta",
    role: "Clinic Owner · New Delhi",
    av: "#FEE2E2",
    ic: "#B91C1C",
    init: "PM",
  },
  {
    type: "Restaurant",
    quote:
      "Saturday dinner rush used to flood our phone line. We'd miss 12-15 reservation calls per evening. Now the AI takes every reservation, confirms it, and sends an SMS. Our occupancy is up 23%.",
    name: "Rajan Sood",
    role: "Owner · Spice Garden, Mumbai",
    av: "#D1FAE5",
    ic: "#065F46",
    init: "RS",
  },
  {
    type: "Salon",
    quote:
      "Setup took 18 minutes. I uploaded my service menu and price list, connected my number, and it was live. The agent knows our services better than our new joinees do. Genuinely shocked.",
    name: "Ananya Kapoor",
    role: "Manager · StyleHub Salons, Bangalore",
    av: "#EDE9FE",
    ic: "#5B21B6",
    init: "AK",
  },
];

function TestimonialCard({ t }) {
  const [hover, setHover] = useS4(false);
  return (
    <M4.div
      whileHover={{ y: -2 }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: "relative",
        background: "#fff",
        border: `1px solid ${hover ? "#C8C3BE" : "#E8E3DE"}`,
        borderRadius: 20,
        padding: 28,
        transition: "border-color 200ms",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <span
        style={{
          position: "absolute",
          top: 16,
          left: 24,
          fontSize: 72,
          fontWeight: 900,
          color: "#F04E00",
          opacity: 0.15,
          lineHeight: 1,
          zIndex: 0,
        }}
      >
        &ldquo;
      </span>
      <div
        style={{
          position: "relative",
          zIndex: 1,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <div style={{ display: "flex", gap: 3 }}>
          {[0, 1, 2, 3, 4].map((i) => (
            <Star key={i} size={14} />
          ))}
        </div>
        <span
          style={{
            background: "#F8F5F1",
            color: "#6B6560",
            fontSize: 11,
            fontWeight: 600,
            padding: "4px 10px",
            borderRadius: 100,
          }}
        >
          {t.type}
        </span>
      </div>
      <p
        style={{
          position: "relative",
          zIndex: 1,
          fontSize: 15,
          color: "#1C1C1C",
          lineHeight: 1.7,
          fontStyle: "italic",
          flex: 1,
          marginTop: 0,
        }}
      >
        {t.quote}
      </p>
      <div
        style={{
          marginTop: 20,
          borderTop: "1px solid #F4F0EC",
          paddingTop: 16,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            background: t.av,
            color: t.ic,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {t.init}
        </span>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#111" }}>{t.name}</div>
          <div style={{ fontSize: 12, color: "#A09890", marginTop: 1 }}>{t.role}</div>
        </div>
      </div>
    </M4.div>
  );
}

function Testimonials() {
  const mobile = useMobile();
  return (
    <section style={{ background: "#fff", ...SECTION_PY }}>
      <div style={wrapPad(mobile)}>
        <div
          style={{
            textAlign: "center",
            maxWidth: 560,
            margin: "0 auto",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Eyebrow text="Customer stories" />
          <Heading2 style={{ textAlign: "center" }}>
            Teams running on <span className="hl">automation</span>.
          </Heading2>
          <p style={{ fontSize: 18, lineHeight: 1.72, color: "#6B6560", marginTop: 20 }}>
            Real businesses. Real results. See what happens when your phone line never goes
            unanswered.
          </p>
        </div>
        <Stagger
          style={{
            display: "grid",
            gridTemplateColumns: mobile ? "1fr" : "repeat(3,1fr)",
            gap: 20,
            marginTop: 48,
            alignItems: "stretch",
          }}
        >
          {TESTIMONIALS.map((t) => (
            <SI key={t.name} style={{ height: "100%" }}>
              <TestimonialCard t={t} />
            </SI>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ---------- FAQ ---------- */
const FAQS = [
  {
    q: "How does the AI agent understand my business?",
    a: "During setup, you upload your service menu, FAQ document, pricing sheet, or website URL. The agent reads and indexes all of it within 2 minutes. From that point, it can answer any question a customer asks that\u2019s covered in your documents. You can update it anytime by uploading a new document.",
  },
  {
    q: "What happens when the AI cannot answer a question?",
    a: "When the agent encounters a question it cannot confidently answer, it politely tells the caller it will connect them to a team member and transfers the call to your configured human fallback number. It can also send you an SMS or email alert with the caller\u2019s question.",
  },
  {
    q: "Can it actually book appointments in my calendar?",
    a: "Yes — on Growth and Pro plans, you connect your Google Calendar during setup. The agent checks real-time availability and books confirmed appointments directly into your calendar. The caller receives an SMS confirmation. You receive a notification.",
  },
  {
    q: "What languages does it support?",
    a: "Currently the agent operates in Indian English. Hindi and Hinglish support is in active development and will be available in a future update. We will notify all subscribers when it launches.",
  },
  {
    q: "How is this different from an IVR or press-1-for-support system?",
    a: "Night and day different. An IVR forces callers through rigid menus. Our agent has a real conversation — the caller speaks naturally, asks anything, and the agent understands and responds intelligently. There is no menu. There are no options. It is a real conversation.",
  },
  {
    q: "Is there a setup fee or contract?",
    a: "No setup fee and no long-term contract. You pay monthly and can cancel anytime from your dashboard. Every plan starts with a 7-day free trial — no credit card required to start.",
  },
  {
    q: "What happens to call recordings and transcripts?",
    a: "Every call is logged with a full transcript and a post-call summary in your client dashboard. Call recordings are stored for 30 days by default. All data is stored in India (ap-south-1 region) and is fully compliant with India\u2019s DPDP Act.",
  },
  {
    q: "How many calls can it handle simultaneously?",
    a: "Starter handles up to 5 simultaneous calls. Growth handles 10. Pro handles 20. If you need higher concurrency for a large practice or busy restaurant chain, contact us for an Enterprise plan.",
  },
];

function FAQItem({ item, open, onToggle }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #E8E3DE",
        borderRadius: 14,
        marginBottom: 8,
        overflow: "hidden",
      }}
    >
      <button
        onClick={onToggle}
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "20px 24px",
          cursor: "pointer",
          background: "transparent",
          border: "none",
          textAlign: "left",
          gap: 16,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 600, color: "#111" }}>{item.q}</span>
        <M4.span
          animate={{ rotate: open ? 45 : 0 }}
          transition={{ duration: 0.2 }}
          style={{ flexShrink: 0, color: open ? "#F04E00" : "#111", display: "inline-flex" }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
        </M4.span>
      </button>
      <AP4 initial={false}>
        {open && (
          <M4.div
            key="faq-panel"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            style={{ overflow: "hidden" }}
          >
            <div
              style={{
                padding: "16px 24px 20px",
                borderTop: "1px solid #E8E3DE",
                fontSize: 14,
                color: "#6B6560",
                lineHeight: 1.7,
              }}
            >
              {item.a}
            </div>
          </M4.div>
        )}
      </AP4>
    </div>
  );
}

function FAQ() {
  const mobile = useMobile();
  const [open, setOpen] = useS4(null);
  return (
    <section
      id="faq"
      style={{ background: "#F8F5F1", ...SECTION_PY, paddingTop: "clamp(32px,4vw,52px)" }}
    >
      <div style={wrapPad(mobile)}>
        <div
          style={{
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Eyebrow text="Common questions" />
          <Heading2 style={{ textAlign: "center" }}>
            Everything you need <span className="hl">to know</span>.
          </Heading2>
        </div>
        <div style={{ maxWidth: 720, margin: "48px auto 0" }}>
          {FAQS.map((f, i) => (
            <FAQItem
              key={i}
              item={f}
              open={open === i}
              onToggle={() => setOpen(open === i ? null : i)}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export { Pricing, Testimonials, FAQ };
