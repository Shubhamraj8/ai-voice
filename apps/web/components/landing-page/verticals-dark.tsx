// @ts-nocheck
"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Eyebrow, Heading2, Stagger, SI, Icon, FadeUp, CountUp } from "./lib";
import { useMobile, wrapPad, SECTION_PY } from "./mid";

const useS3 = useState,
  useE3 = useEffect,
  useR3 = useRef;
const M3 = motion;

/* ============================================================
   verticals-dark.jsx — Verticals grid, Dark feature showcase
   ============================================================ */

/* ---------- VERTICALS ---------- */
const VERTICALS = [
  {
    icon: "medical",
    cat: "Healthcare",
    t: "Clinics & Hospitals",
    d: "Book appointments, handle patient queries, manage doctor schedules, and reduce front desk workload by 80%.",
    tags: ["Appointment booking", "Patient FAQs", "Doctor availability"],
  },
  {
    icon: "food",
    cat: "F&B",
    t: "Restaurants & Cafes",
    d: "Take table reservations, answer menu questions, handle peak-hour call floods without a single missed booking.",
    tags: ["Reservations", "Menu queries", "Peak hour handling"],
  },
  {
    icon: "bed",
    cat: "Hospitality",
    t: "Hotels & Guest Houses",
    d: "Answer availability queries, handle check-in timing questions, upsell services, and take room bookings.",
    tags: ["Room availability", "Check-in info", "Amenities"],
  },
  {
    icon: "cart",
    cat: "Retail",
    t: "Retail Stores & Marts",
    d: "Answer store hours, check product availability, handle return queries, and direct customers to right departments.",
    tags: ["Store hours", "Stock queries", "Customer support"],
  },
  {
    icon: "scissors",
    cat: "Beauty & Wellness",
    t: "Salons & Spas",
    d: "Book appointments for stylists, answer service duration and pricing questions, manage walk-in queues over phone.",
    tags: ["Stylist booking", "Service pricing", "Wait times"],
  },
  {
    icon: "pill",
    cat: "Healthcare",
    t: "Pharmacies & Diagnostic Labs",
    d: "Answer medicine availability queries, book diagnostic test slots, handle prescription refill reminder calls.",
    tags: ["Medicine queries", "Test bookings", "Refill reminders"],
  },
];

function VerticalCard({ v }) {
  const [hover, setHover] = useS3(false);
  return (
    <M3.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: "#fff",
        border: `1px solid ${hover ? "#F04E00" : "#E8E3DE"}`,
        borderRadius: 16,
        padding: 24,
        cursor: "pointer",
        boxShadow: hover ? "0 0 0 3px rgba(240,78,0,0.06)" : "none",
        transition: "border-color 200ms, box-shadow 200ms",
        height: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 16,
        }}
      >
        <M3.div
          animate={hover ? { rotate: -8, scale: 1.1 } : { rotate: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: hover ? "#FFF4EE" : "#F8F5F1",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "background 200ms",
          }}
        >
          <Icon name={v.icon} size={22} stroke={hover ? "#F04E00" : "#6B6560"} />
        </M3.div>
        <span
          style={{ fontSize: 16, color: hover ? "#F04E00" : "#E8E3DE", transition: "color 200ms" }}
        >
          →
        </span>
      </div>
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.10em",
          textTransform: "uppercase",
          color: "#A09890",
          marginBottom: 6,
        }}
      >
        {v.cat}
      </div>
      <div style={{ fontSize: 17, fontWeight: 700, color: "#111" }}>{v.t}</div>
      <p
        style={{ fontSize: 13, color: "#6B6560", lineHeight: 1.55, marginTop: 6, marginBottom: 0 }}
      >
        {v.d}
      </p>
      <div
        style={{
          marginTop: 16,
          borderTop: "1px solid #F4F0EC",
          paddingTop: 14,
          display: "flex",
          flexWrap: "wrap",
          gap: 6,
        }}
      >
        {v.tags.map((t) => (
          <span
            key={t}
            style={{
              background: "#F4F0EC",
              color: "#6B6560",
              fontSize: 11,
              fontWeight: 500,
              padding: "3px 8px",
              borderRadius: 100,
            }}
          >
            {t}
          </span>
        ))}
      </div>
    </M3.div>
  );
}

function Verticals() {
  const mobile = useMobile();
  const [w, setW] = useS3(1200);
  useE3(() => {
    const r = () => setW(window.innerWidth);
    r();
    window.addEventListener("resize", r);
    return () => window.removeEventListener("resize", r);
  }, []);
  const cols = w <= 640 ? 1 : w <= 1024 ? 2 : 3;
  const scrollMode = w <= 640;

  return (
    <section id="verticals" style={{ background: "#fff", ...SECTION_PY }}>
      <div style={wrapPad(mobile)}>
        <div
          style={{
            textAlign: "center",
            maxWidth: 600,
            margin: "0 auto",
            marginBottom: 48,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Eyebrow text="Built for every business" />
          <Heading2 style={{ textAlign: "center" }}>
            One agent. <span className="hl">Every vertical.</span>
          </Heading2>
          <p style={{ fontSize: 18, lineHeight: 1.72, color: "#6B6560", marginTop: 20 }}>
            Whether you run a 3-table restaurant or a multi-doctor clinic, your AI voice agent
            adapts to your business type automatically.
          </p>
        </div>

        {scrollMode ? (
          <>
            <div
              className="no-scrollbar"
              style={{
                display: "flex",
                gap: 16,
                overflowX: "auto",
                paddingBottom: 8,
                scrollSnapType: "x mandatory",
              }}
            >
              {VERTICALS.map((v) => (
                <div key={v.t} style={{ width: 260, flexShrink: 0, scrollSnapAlign: "start" }}>
                  <VerticalCard v={v} />
                </div>
              ))}
            </div>
            <div style={{ textAlign: "center", fontSize: 13, color: "#A09890", marginTop: 12 }}>
              swipe →
            </div>
          </>
        ) : (
          <Stagger style={{ display: "grid", gridTemplateColumns: `repeat(${cols},1fr)`, gap: 16 }}>
            {VERTICALS.map((v) => (
              <SI key={v.t} style={{ height: "100%" }}>
                <VerticalCard v={v} />
              </SI>
            ))}
          </Stagger>
        )}
      </div>
    </section>
  );
}

/* ---------- DARK FEATURE SHOWCASE ---------- */
const DARK_CARDS = [
  {
    icon: "slider",
    tag: "Voice Engine",
    t: "Fully configurable personality",
    d: "Define your agent's name, tone, language style, and guardrails. A dental clinic needs clinical precision; a restaurant wants warmth. Your agent reflects your brand, not ours.",
  },
  {
    icon: "shield",
    tag: "Infrastructure",
    t: "Production-grade reliability",
    d: "Built on Pipecat voice orchestration, Deepgram transcription, and enterprise-grade cloud infra. Sub-1.2 second response per turn. 99.9% uptime SLA on Pro plans.",
  },
  {
    icon: "brain",
    tag: "Intelligence",
    t: "Smarter with every interaction",
    d: "Every call transcript is logged and searchable. Upload new documents anytime and your agent learns within minutes. The more you give it, the better it gets.",
  },
];

function DarkCard({ c }) {
  const [hover, setHover] = useS3(false);
  return (
    <M3.div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      whileHover={{
        y: -2,
        borderColor: "#3A3634",
        boxShadow: "0 0 0 1px rgba(240,78,0,0.15), 0 16px 40px rgba(0,0,0,0.4)",
      }}
      style={{
        background: "#161616",
        border: "1px solid #2A2826",
        borderRadius: 20,
        padding: 28,
        position: "relative",
        overflow: "hidden",
        height: "100%",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.05) 50%, transparent 60%)",
          backgroundSize: "200% 100%",
          backgroundPosition: hover ? "-100% 0" : "200% 0",
          transition: "background-position 700ms ease",
          pointerEvents: "none",
        }}
      />
      <div style={{ position: "relative" }}>
        <M3.div
          animate={hover ? { rotate: -8, scale: 1.1 } : {}}
          transition={{ type: "spring", stiffness: 400, damping: 20 }}
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: "rgba(240,78,0,0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon name={c.icon} size={20} stroke="#F04E00" />
        </M3.div>
        <span
          style={{
            display: "inline-block",
            marginTop: 16,
            background: "rgba(240,78,0,0.1)",
            color: "#F04E00",
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.08em",
            padding: "3px 9px",
            borderRadius: 100,
            textTransform: "uppercase",
          }}
        >
          {c.tag}
        </span>
        <div style={{ fontSize: 19, fontWeight: 700, color: "#fff", marginTop: 10 }}>{c.t}</div>
        <p
          style={{
            fontSize: 14,
            color: "#7A7370",
            lineHeight: 1.65,
            marginTop: 10,
            marginBottom: 0,
          }}
        >
          {c.d}
        </p>
      </div>
    </M3.div>
  );
}

function AgentDashboard() {
  const items = [
    {
      n: "1",
      bg: "#1E3A2E",
      nc: "#4A9E6A",
      t: "Low Impact: 2 FAQ queries resolved automatically",
      s: "Store hours + menu price questions — no human needed",
      r: "saved 4:20",
      rc: "#4A9E6A",
    },
    {
      n: "2",
      bg: "rgba(240,78,0,0.15)",
      nc: "#F04E00",
      t: "Revenue Driver: New appointment booked — ₹2,400",
      s: "Priya Sharma → Dr. Mehta · Monday 11:00 AM",
      r: "just now",
      rc: "#F04E00",
    },
    {
      n: "3",
      bg: "rgba(107,143,191,0.15)",
      nc: "#6B8FBF",
      t: "Repetitive: Directions query automated",
      s: "Address + parking info sent via SMS",
      r: "11 mins ago",
      rc: "#5A5654",
    },
  ];
  const ref = useR3(null);
  return (
    <M3.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.8 }}
      style={{
        background: "#111",
        border: "1px solid #2A2826",
        borderRadius: 20,
        overflow: "hidden",
        maxWidth: 680,
        margin: "clamp(36px,6vw,64px) auto 0",
      }}
    >
      <div
        style={{
          background: "#161616",
          borderBottom: "1px solid #2A2826",
          padding: "13px 18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", gap: 7, flexShrink: 0 }}>
          {["#3A3838", "#3A3838", "#3A3838"].map((c, i) => (
            <span key={i} style={{ width: 11, height: 11, borderRadius: "50%", background: c }} />
          ))}
        </div>
        <span
          className="mono"
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "#5A5654",
            flex: 1,
            textAlign: "center",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            minWidth: 0,
          }}
        >
          ZERQO Agent Dashboard
        </span>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: "#4A9E6A",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          <M3.span
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "#4A9E6A",
              flexShrink: 0,
            }}
          />
          3 active calls
        </span>
      </div>
      <div style={{ padding: 20 }}>
        {items.map((it, i) => (
          <div
            key={it.n}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 14,
              padding: "14px 0",
              borderBottom: i < items.length - 1 ? "1px solid #1E1E1E" : "none",
            }}
          >
            <span
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: it.bg,
                color: it.nc,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {it.n}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#fff" }}>{it.t}</div>
              <div style={{ fontSize: 12, color: "#5A5654", marginTop: 2 }}>{it.s}</div>
            </div>
            <span style={{ fontSize: 11, color: it.rc, fontWeight: 600, whiteSpace: "nowrap" }}>
              {it.r}
            </span>
          </div>
        ))}
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 16 }}>
          <button
            style={{
              border: "1px solid #2A2826",
              background: "transparent",
              color: "#5A5654",
              fontSize: 12,
              fontWeight: 500,
              padding: "8px 14px",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Export report
          </button>
          <button
            style={{
              border: "none",
              background: "#F04E00",
              color: "#fff",
              fontSize: 12,
              fontWeight: 600,
              padding: "8px 16px",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            View all calls →
          </button>
        </div>
      </div>
    </M3.div>
  );
}

function DarkShowcase() {
  const mobile = useMobile();
  return (
    <section
      style={{ background: "#0D0D0D", ...SECTION_PY, position: "relative", overflow: "hidden" }}
    >
      <M3.div
        style={{
          position: "absolute",
          top: -100,
          left: -100,
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "radial-gradient(circle at center, rgba(240,78,0,0.10) 0%, transparent 70%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
        animate={{ x: [0, 80, 0], y: [0, 60, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <M3.div
        style={{
          position: "absolute",
          top: 0,
          right: -80,
          width: 500,
          height: 500,
          borderRadius: "50%",
          background:
            "radial-gradient(circle at center, rgba(240,120,50,0.07) 0%, transparent 70%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
        animate={{ x: [0, -60, 0], y: [0, 80, 0] }}
        transition={{ duration: 22, repeat: Infinity, delay: 2, ease: "easeInOut" }}
      />
      <M3.div
        style={{
          position: "absolute",
          bottom: 0,
          left: "50%",
          width: 400,
          height: 400,
          borderRadius: "50%",
          background:
            "radial-gradient(circle at center, rgba(255,255,255,0.03) 0%, transparent 70%)",
          pointerEvents: "none",
          zIndex: 0,
        }}
        animate={{ y: [0, -40, 0] }}
        transition={{ duration: 14, repeat: Infinity, delay: 4, ease: "easeInOut" }}
      />

      <div style={{ position: "relative", zIndex: 1, ...wrapPad(mobile) }}>
        <div
          style={{
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Eyebrow text="Platform capabilities" dark />
          <FadeUp>
            <div
              className="display"
              style={{
                fontSize: "clamp(48px,12vw,120px)",
                fontWeight: 700,
                letterSpacing: "-0.05em",
                color: "#F04E00",
                lineHeight: 1,
                textAlign: "center",
                whiteSpace: "nowrap",
              }}
            >
              <CountUp end={240000} suffix="+" />
            </div>
            <p
              style={{
                fontSize: 18,
                color: "rgba(255,255,255,0.5)",
                textAlign: "center",
                marginTop: 8,
              }}
            >
              minutes of calls automated for Indian businesses
            </p>
          </FadeUp>
        </div>

        <Stagger
          style={{
            display: "grid",
            gridTemplateColumns: mobile ? "1fr" : "repeat(3,1fr)",
            gap: 20,
            marginTop: 64,
          }}
        >
          {DARK_CARDS.map((c) => (
            <SI key={c.t} style={{ height: "100%" }}>
              <DarkCard c={c} />
            </SI>
          ))}
        </Stagger>

        <AgentDashboard />
      </div>
    </section>
  );
}

export { Verticals, DarkShowcase };
