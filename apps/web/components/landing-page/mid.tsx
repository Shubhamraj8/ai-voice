// @ts-nocheck
"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import { EASE_OUT_EXPO, FadeUp, Stagger, SI, Eyebrow, Heading2, Icon, CountUp } from "./lib";

const useS2 = useState,
  useE2 = useEffect,
  useR2 = useRef;
const M2 = motion,
  AP2 = AnimatePresence,
  useIV2 = useInView;

/* ============================================================
   mid.jsx — Social proof, Value prop + call terminal, Stats, How it works
   ============================================================ */

const SECTION_PY = {
  paddingTop: "clamp(72px,11vw,128px)",
  paddingBottom: "clamp(72px,11vw,128px)",
};
const wrap = (mobile) => ({
  maxWidth: 1100,
  margin: "0 auto",
  padding: mobile ? "0 20px" : "0 80px",
});
const MOBILE_BP = 900;
function useViewport() {
  const [w, setW] = useS2(typeof window !== "undefined" ? window.innerWidth : 1200);
  useE2(() => {
    let raf = 0;
    const r = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setW(window.innerWidth));
    };
    r();
    window.addEventListener("resize", r);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", r);
    };
  }, []);
  return w;
}
function useMobile() {
  return useViewport() <= MOBILE_BP;
}

/* ---------- SOCIAL PROOF / LOGOS ---------- */
function SocialProof() {
  const mobile = useMobile();
  const logos = [
    { t: "MediCare+", s: { fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" } },
    {
      t: "Spice Garden",
      s: { fontSize: 16, fontWeight: 400, letterSpacing: "0.06em", textTransform: "uppercase" },
    },
    { t: "GrandStay", s: { fontSize: 18, fontWeight: 800 } },
    { t: "FreshMart", s: { fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em" } },
    {
      t: "StyleHub",
      s: { fontSize: 16, fontWeight: 300, letterSpacing: "0.12em", textTransform: "uppercase" },
    },
  ];
  return (
    <section
      style={{
        background: "#fff",
        padding: "48px 0",
        borderTop: "1px solid #E8E3DE",
        borderBottom: "1px solid #E8E3DE",
      }}
    >
      <div style={wrap(mobile)}>
        <p
          style={{
            textAlign: "center",
            fontSize: 13,
            fontWeight: 500,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "#A09890",
            marginBottom: 32,
            marginTop: 0,
          }}
        >
          Trusted by forward-thinking Indian businesses
        </p>
        <Stagger
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: mobile ? 20 : 32,
            flexWrap: "wrap",
          }}
        >
          {logos.map((l, i) => (
            <SI key={l.t} style={{ display: "flex", alignItems: "center", gap: mobile ? 20 : 32 }}>
              <span style={{ color: "#C8C3BE", ...l.s }}>{l.t}</span>
              {i < logos.length - 1 && !mobile && (
                <span style={{ width: 1, height: 20, background: "#E8E3DE" }} />
              )}
            </SI>
          ))}
        </Stagger>
      </div>
    </section>
  );
}

/* ---------- CALL TERMINAL ---------- */
const CALL_LINES = [
  { who: "CALLER", msg: "Hi, I need to book a dental cleaning for Monday" },
  {
    who: "AGENT",
    msg: "Of course! I have 10 AM and 2 PM available this Monday with Dr. Sharma. Which works for you?",
  },
  { who: "CALLER", msg: "2 PM please." },
  { who: "AGENT", msg: "Perfect! Can I get your name and phone number to confirm?" },
  { who: "CALLER", msg: "Priya Sharma, 9876543210" },
  {
    who: "AGENT",
    msg: "Booking confirmed for Monday 2:00 PM — Dr. Sharma, dental cleaning. Sending you a confirmation SMS now.",
  },
  { who: "SYS_OK", msg: "Appointment booked · Dr. Sharma · Monday 2:00 PM" },
  { who: "SYS_SMS", msg: "SMS confirmation sent to +91 98765 43210" },
];

function CallTerminal() {
  const ref = useR2(null);
  const inView = useIV2(ref, { once: true, amount: 0.4 });
  const [shown, setShown] = useS2(0);
  const [run, setRun] = useS2(0);

  useE2(() => {
    if (!inView && run === 0) return;
    setShown(0);
    let i = 0;
    const timers = [];
    const tick = () => {
      i += 1;
      setShown(i);
      if (i < CALL_LINES.length) timers.push(setTimeout(tick, i % 2 === 0 ? 900 : 700));
    };
    timers.push(setTimeout(tick, 400));
    return () => timers.forEach(clearTimeout);
  }, [inView, run]);

  const pill = {
    fontSize: 9,
    fontWeight: 700,
    letterSpacing: "0.08em",
    padding: "2px 7px",
    borderRadius: 4,
    flexShrink: 0,
  };

  return (
    <M2.div
      ref={ref}
      initial={{ opacity: 0, x: 24 }}
      animate={inView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 1 }}
      style={{
        background: "#fff",
        border: "1px solid #E8E3DE",
        borderRadius: 20,
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {/* header */}
      <div
        style={{
          background: "#F4F0EC",
          borderBottom: "1px solid #E8E3DE",
          padding: "13px 18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
          {["#F05252", "#F0B429", "#16A34A"].map((c) => (
            <span key={c} style={{ width: 12, height: 12, borderRadius: "50%", background: c }} />
          ))}
        </div>
        <span
          className="mono"
          style={{
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: "0.02em",
            color: "#6B6560",
            flex: 1,
            textAlign: "center",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            minWidth: 0,
          }}
        >
          AI Voice Agent · Active Call
        </span>
        <span style={{ position: "relative", display: "inline-flex", flexShrink: 0 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#16A34A" }} />
          <M2.span
            animate={{ scale: [1, 2.5], opacity: [0.4, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            style={{ position: "absolute", inset: -4, borderRadius: "50%", background: "#16A34A" }}
          />
        </span>
      </div>

      {/* body */}
      <div
        className="mono"
        style={{
          padding: "24px 24px 20px",
          background: "#fff",
          fontSize: 13,
          lineHeight: 1.7,
          minHeight: 380,
        }}
      >
        <AP2>
          {CALL_LINES.slice(0, shown).map((l, i) => {
            if (l.who === "SYS_OK")
              return (
                <M2.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    background: "#F0FDF4",
                    borderRadius: 8,
                    padding: "8px 12px",
                    borderLeft: "3px solid #16A34A",
                    margin: "8px 0",
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                  }}
                >
                  <Icon name="check" size={14} stroke="#16A34A" sw={2.5} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#16A34A" }}>{l.msg}</span>
                </M2.div>
              );
            if (l.who === "SYS_SMS")
              return (
                <M2.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    background: "#FFF4EE",
                    borderRadius: 8,
                    padding: "8px 12px",
                    borderLeft: "3px solid #F04E00",
                    margin: "4px 0",
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                  }}
                >
                  <Icon name="sms" size={14} stroke="#F04E00" />
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#F04E00" }}>{l.msg}</span>
                </M2.div>
              );
            const agent = l.who === "AGENT";
            return (
              <M2.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  display: "flex",
                  gap: 10,
                  alignItems: "flex-start",
                  padding: "5px 0",
                  borderBottom: "1px solid rgba(232,227,222,0.5)",
                }}
              >
                <span
                  style={{
                    ...pill,
                    background: agent ? "#FFF4EE" : "#F4F0EC",
                    color: agent ? "#F04E00" : "#A09890",
                  }}
                >
                  {l.who}
                </span>
                <span style={{ color: agent ? "#111" : "#6B6560", fontWeight: agent ? 500 : 400 }}>
                  {l.msg}
                </span>
              </M2.div>
            );
          })}
        </AP2>
        {shown >= CALL_LINES.length && (
          <button
            onClick={() => setRun((r) => r + 1)}
            style={{
              marginTop: 12,
              fontSize: 12,
              color: "#A09890",
              border: "none",
              background: "none",
              cursor: "pointer",
            }}
          >
            ↺ Replay demo
          </button>
        )}
      </div>

      {/* footer */}
      <div
        style={{
          background: "#F8F5F1",
          borderTop: "1px solid #E8E3DE",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <span className="mono" style={{ fontSize: 12, color: "#A09890" }}>
          Total call duration: 1:42
        </span>
        <span
          style={{
            background: "#FFF4EE",
            color: "#F04E00",
            fontSize: 11,
            fontWeight: 600,
            padding: "4px 12px",
            borderRadius: 100,
            border: "1px solid rgba(240,78,0,0.2)",
          }}
        >
          Call resolved · No transfer needed
        </span>
      </div>
    </M2.div>
  );
}

/* ---------- VALUE PROP / DEMO ---------- */
function ValueProp() {
  const mobile = useMobile();
  const bullets = [
    {
      icon: "phone",
      t: "Instant answer, every time",
      d: "Picks up within 1 ring, 24 hours a day, 365 days a year",
    },
    {
      icon: "calendar",
      t: "Books appointments automatically",
      d: "Checks your Google Calendar and books slots in real time",
    },
    {
      icon: "upload",
      t: "Trained on your knowledge",
      d: "Upload your FAQs, menu, or service list — it knows it all",
    },
    {
      icon: "transfer",
      t: "Escalates when needed",
      d: "Transfers to you or sends an SMS when the call needs a human",
    },
  ];
  return (
    <section id="features" style={{ background: "#F8F5F1", ...SECTION_PY }}>
      <div style={wrap(mobile)}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: mobile ? "1fr" : "1fr 1fr",
            gap: mobile ? 48 : 64,
            alignItems: "start",
          }}
        >
          <FadeUp>
            <Eyebrow text="How it works" />
            <Heading2>
              Your business calls,
              <br />
              handled by <span className="hl">intelligence</span>.
            </Heading2>
            <p
              style={{
                fontSize: 17,
                lineHeight: 1.72,
                color: "#6B6560",
                maxWidth: 440,
                marginTop: 22,
                marginBottom: 32,
              }}
            >
              Your AI voice agent knows everything about your business — your services, opening
              hours, pricing, FAQs, and calendar availability. When a customer calls, it picks up
              instantly, speaks naturally, and either resolves the query or books the appointment.
              No hold time. No missed calls. No extra payroll.
            </p>
            <Stagger style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {bullets.map((b) => (
                <SI key={b.t}>
                  <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: "50%",
                        background: "#FFF4EE",
                        flexShrink: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <Icon name={b.icon} size={18} stroke="#F04E00" />
                    </div>
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 600, color: "#111" }}>{b.t}</div>
                      <div style={{ fontSize: 14, color: "#6B6560", marginTop: 2 }}>{b.d}</div>
                    </div>
                  </div>
                </SI>
              ))}
            </Stagger>
          </FadeUp>
          <CallTerminal />
        </div>
      </div>
    </section>
  );
}

/* ---------- STATS ---------- */
function Stats() {
  const mobile = useMobile();
  const stats = [
    {
      num: <CountUp end={14000} prefix="₹" suffix="+" />,
      label: "Lost per missed appointment",
      sub: "Average Indian clinic",
    },
    {
      num: <CountUp end={1.2} suffix="s" />,
      label: "Response time per turn",
      sub: "Fastest in category",
    },
    {
      num: <CountUp end={94} suffix="%" />,
      label: "First-call resolution rate",
      sub: "No human needed",
    },
    { num: <CountUp end={0} prefix="₹" />, label: "Setup cost", sub: "Start in 30 minutes" },
  ];
  return (
    <section
      style={{
        background: "#fff",
        borderTop: "1px solid #E8E3DE",
        borderBottom: "1px solid #E8E3DE",
      }}
    >
      <div
        style={{
          ...wrap(mobile),
          display: "grid",
          gridTemplateColumns: mobile ? "1fr 1fr" : "repeat(4, minmax(0, 1fr))",
        }}
      >
        {stats.map((s, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              padding: mobile ? "32px 12px" : "48px 24px",
              borderLeft: !mobile && i > 0 ? "1px solid #E8E3DE" : "none",
              borderTop: mobile && i >= 2 ? "1px solid #E8E3DE" : "none",
              borderLeftWidth: mobile && i % 2 === 1 ? 1 : !mobile && i > 0 ? 1 : 0,
              borderLeftStyle: "solid",
              borderLeftColor: "#E8E3DE",
            }}
          >
            <div
              className="display"
              style={{
                fontSize: mobile ? "clamp(28px,8.5vw,40px)" : 56,
                fontWeight: 700,
                letterSpacing: "-0.04em",
                color: "#F04E00",
                lineHeight: 1,
                minHeight: mobile ? "clamp(28px,8.5vw,40px)" : 56,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {s.num}
            </div>
            <div
              style={{
                fontSize: mobile ? 14 : 15,
                fontWeight: 600,
                color: "#111",
                marginTop: 8,
                textWrap: "balance",
              }}
            >
              {s.label}
            </div>
            <div style={{ fontSize: 13, color: "#A09890", marginTop: 4 }}>{s.sub}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------- HOW IT WORKS (sticky stepper) ---------- */
const STEPS = [
  {
    n: "01",
    t: "Connect your phone number",
    d: "Buy a new number or connect your existing one. We provision it instantly. Your AI agent is now reachable on a real Indian phone number.",
  },
  {
    n: "02",
    t: "Train with your business knowledge",
    d: "Upload your service menu, FAQ document, price list, or website URL. Your agent reads and learns it all in under 2 minutes. No prompting or configuration required.",
  },
  {
    n: "03",
    t: "Go live — answer every call",
    d: "Flip the switch. Your AI receptionist is now answering every inbound call, booking appointments, and handling customers — completely automatically.",
  },
];

function StepVisual({ index }) {
  const chrome = (
    <div
      style={{
        background: "#F4F0EC",
        borderBottom: "1px solid #E8E3DE",
        padding: "12px 18px",
        display: "flex",
        gap: 7,
      }}
    >
      {["#F05252", "#F0B429", "#16A34A"].map((c) => (
        <span key={c} style={{ width: 11, height: 11, borderRadius: "50%", background: c }} />
      ))}
    </div>
  );
  const panelStyle = {
    background: "#fff",
    border: "1px solid #E8E3DE",
    borderRadius: 20,
    overflow: "hidden",
    minHeight: 380,
  };
  const row = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 14px",
    borderRadius: 10,
    fontSize: 13,
  };

  const panels = [
    /* Panel 1 — phone selection */
    <div style={panelStyle} key="p1">
      {chrome}
      <div style={{ padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: "#111", marginBottom: 16 }}>
          Select phone number
        </div>
        {[
          { n: "+91 98100 XXXXX", c: "New Delhi, IN", sel: false },
          { n: "+91 80200 XXXXX", c: "Bangalore, IN", sel: true },
          { n: "+91 22300 XXXXX", c: "Mumbai, IN", sel: false },
        ].map((o) => (
          <div
            key={o.n}
            style={{
              ...row,
              background: o.sel ? "#FFF4EE" : "#F8F5F1",
              border: `1px solid ${o.sel ? "rgba(240,78,0,0.25)" : "#E8E3DE"}`,
              marginBottom: 10,
            }}
          >
            <span>
              <span style={{ fontWeight: 600, color: "#111" }}>{o.n}</span>{" "}
              <span style={{ color: "#A09890" }}>— {o.c}</span>
            </span>
            <span
              style={{
                width: 18,
                height: 18,
                borderRadius: "50%",
                border: `2px solid ${o.sel ? "#F04E00" : "#D0C9C2"}`,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {o.sel && (
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#F04E00" }} />
              )}
            </span>
          </div>
        ))}
        <button
          style={{
            width: "100%",
            marginTop: 8,
            background: "#F04E00",
            color: "#fff",
            border: "none",
            borderRadius: 100,
            padding: "12px",
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Provision Number →
        </button>
      </div>
    </div>,
    /* Panel 2 — knowledge upload */
    <div style={panelStyle} key="p2">
      {chrome}
      <div style={{ padding: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: "#111", marginBottom: 16 }}>
          Train your AI agent
        </div>
        <div
          style={{
            border: "2px dashed #E8E3DE",
            borderRadius: 12,
            padding: 28,
            textAlign: "center",
            marginBottom: 16,
          }}
        >
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
            <Icon name="cloud" size={40} stroke="#A09890" />
          </div>
          <div style={{ fontSize: 13, color: "#A09890" }}>
            Drop your FAQ, menu, or service document here
          </div>
        </div>
        {[
          { ic: "pdf", n: "Services & Pricing.pdf", st: "Trained", done: true },
          { ic: "pdf", n: "Opening Hours & FAQs.pdf", st: "Trained", done: true },
          { ic: "link", n: "google.com/… (website scraped)", st: "Training…", done: false },
        ].map((d) => (
          <div key={d.n} style={{ ...row, padding: "8px 0" }}>
            <span
              style={{ display: "inline-flex", alignItems: "center", gap: 8, color: "#6B6560" }}
            >
              <Icon name={d.ic} size={16} stroke="#F04E00" />
              {d.n}
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                color: d.done ? "#16A34A" : "#A09890",
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              {d.done ? <Icon name="check" size={12} stroke="#16A34A" sw={2.5} /> : null}
              {d.st}
            </span>
          </div>
        ))}
        <div
          style={{
            marginTop: 14,
            height: 6,
            background: "#F4F0EC",
            borderRadius: 100,
            overflow: "hidden",
          }}
        >
          <M2.div
            initial={{ width: 0 }}
            whileInView={{ width: "78%" }}
            viewport={{ once: true }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            style={{ height: "100%", background: "#F04E00", borderRadius: 100 }}
          />
        </div>
      </div>
    </div>,
    /* Panel 3 — dashboard */
    <div style={panelStyle} key="p3">
      {chrome}
      <div style={{ padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#16A34A" }} />
          <span style={{ fontSize: 14, fontWeight: 600, color: "#111" }}>
            3 calls today · 0 missed
          </span>
        </div>
        {[
          {
            dot: "#16A34A",
            t: "Priya Sharma · Booking confirmed · 1:42",
            tag: "10 AM slot · Dr. Sharma",
            tc: "#F04E00",
            tb: "#FFF4EE",
          },
          {
            dot: "#3B82F6",
            t: "Rahul Mehta · FAQ answered · 0:58",
            tag: "Info query",
            tc: "#6B6560",
            tb: "#F4F0EC",
          },
          {
            dot: "#F04E00",
            t: "Ananya K · Transferred · 3:12",
            tag: "Human needed",
            tc: "#B91C1C",
            tb: "#FEE2E2",
          },
        ].map((r, i) => (
          <div key={i} style={{ ...row, padding: "12px 0", borderBottom: "1px solid #F4F0EC" }}>
            <span
              style={{ display: "inline-flex", alignItems: "center", gap: 10, color: "#1C1C1C" }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: r.dot,
                  flexShrink: 0,
                }}
              />
              {r.t}
            </span>
            <span
              style={{
                background: r.tb,
                color: r.tc,
                fontSize: 11,
                fontWeight: 600,
                padding: "3px 9px",
                borderRadius: 100,
                whiteSpace: "nowrap",
              }}
            >
              {r.tag}
            </span>
          </div>
        ))}
        <div style={{ marginTop: 14, fontSize: 13, color: "#A09890" }}>
          Total minutes saved today: 6:32
        </div>
      </div>
    </div>,
  ];

  return panels[index];
}

function HowItWorks() {
  const mobile = useMobile();
  const [active, setActive] = useS2(0);
  const trackRef = useR2(null);

  /* Scroll-progress drives the active step. The whole stage is pinned
     (sticky) for the section's full scroll length, and the active index
     is derived from how far we've scrolled through the track. */
  useE2(() => {
    if (mobile) return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = trackRef.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const total = el.offsetHeight - window.innerHeight;
        const scrolled = Math.min(Math.max(-rect.top, 0), total);
        const idx =
          total > 0
            ? Math.min(STEPS.length - 1, Math.floor((scrolled / total) * STEPS.length * 0.999))
            : 0;
        setActive(idx);
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [mobile]);

  const jumpTo = (i) => {
    const el = trackRef.current;
    if (!el) return;
    const total = el.offsetHeight - window.innerHeight;
    const top = window.scrollY + el.getBoundingClientRect().top + (i / STEPS.length) * total + 12;
    window.scrollTo({ top, behavior: "smooth" });
  };

  const Header = (
    <div
      style={{
        textAlign: "center",
        maxWidth: 560,
        margin: "0 auto",
        marginBottom: mobile ? 40 : 8,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Eyebrow text="Setup process" />
      <Heading2 style={{ textAlign: "center" }}>
        From signup to <span className="hl">first live call</span> in 30 minutes.
      </Heading2>
      <p style={{ fontSize: 18, lineHeight: 1.72, color: "#6B6560", marginTop: 20 }}>
        No engineers needed. No complex configuration. Upload your business info and go live in
        minutes.
      </p>
    </div>
  );

  if (mobile) {
    return (
      <section id="how" style={{ background: "#F8F5F1", ...SECTION_PY }}>
        <div style={wrap(mobile)}>
          {Header}
          <div style={{ display: "flex", flexDirection: "column", gap: 40, marginTop: 8 }}>
            {STEPS.map((s, i) => (
              <div key={s.n}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: "50%",
                      background: "#F04E00",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                      fontWeight: 700,
                      color: "#fff",
                      flexShrink: 0,
                    }}
                  >
                    {s.n}
                  </span>
                  <div style={{ fontSize: 20, fontWeight: 700, color: "#111" }}>{s.t}</div>
                </div>
                <p
                  style={{
                    fontSize: 15,
                    color: "#6B6560",
                    margin: "12px 0 18px",
                    lineHeight: 1.65,
                  }}
                >
                  {s.d}
                </p>
                <StepVisual index={i} />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  /* ----- DESKTOP: pinned stage; left stepper + right panel swap together ----- */
  return (
    <section id="how" style={{ background: "#F8F5F1", paddingTop: "clamp(72px,11vw,128px)" }}>
      <div style={wrap(mobile)}>{Header}</div>

      {/* tall track gives the pin its scroll length (≈0.8 viewport per step) */}
      <div ref={trackRef} style={{ position: "relative", height: `${STEPS.length * 80}vh` }}>
        <div
          style={{
            position: "sticky",
            top: 64,
            height: "calc(100vh - 64px)",
            display: "flex",
            alignItems: "center",
          }}
        >
          <div style={{ ...wrap(mobile), width: "100%" }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "40% 60%",
                gap: 56,
                alignItems: "center",
              }}
            >
              {/* LEFT — stepper */}
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {STEPS.map((s, i) => {
                  const on = active === i;
                  return (
                    <div
                      key={s.n}
                      onClick={() => jumpTo(i)}
                      style={{
                        position: "relative",
                        padding: "18px 0 18px 26px",
                        borderLeft: `2px solid ${on ? "#F04E00" : "#E4DED8"}`,
                        cursor: "pointer",
                        transition: "border-color 350ms ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <span
                          style={{
                            width: 30,
                            height: 30,
                            borderRadius: "50%",
                            background: on ? "#F04E00" : "#CFC8C1",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: 12,
                            fontWeight: 700,
                            color: "#fff",
                            flexShrink: 0,
                            transition: "background 350ms ease",
                          }}
                        >
                          {s.n}
                        </span>
                        <div
                          style={{
                            fontSize: 22,
                            fontWeight: 700,
                            letterSpacing: "-0.01em",
                            color: on ? "#111" : "#B4ADA6",
                            transition: "color 350ms ease",
                          }}
                        >
                          {s.t}
                        </div>
                      </div>
                      <M2.div
                        initial={false}
                        animate={{ height: on ? "auto" : 0, opacity: on ? 1 : 0 }}
                        transition={{ duration: 0.4, ease: EASE_OUT_EXPO }}
                        style={{ overflow: "hidden" }}
                      >
                        <p
                          style={{
                            fontSize: 15,
                            color: "#6B6560",
                            margin: "12px 0 0",
                            paddingLeft: 42,
                            lineHeight: 1.65,
                            maxWidth: 380,
                          }}
                        >
                          {s.d}
                        </p>
                      </M2.div>
                    </div>
                  );
                })}
              </div>

              {/* RIGHT — panel swaps in sync */}
              <div style={{ position: "relative" }}>
                <AP2 mode="wait">
                  <M2.div
                    key={active}
                    initial={{ opacity: 0, y: 18 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -14 }}
                    transition={{ duration: 0.4, ease: EASE_OUT_EXPO }}
                  >
                    <StepVisual index={active} />
                  </M2.div>
                </AP2>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export { SocialProof, ValueProp, Stats, HowItWorks, SECTION_PY, useMobile, useViewport };
export const wrapPad = wrap;
