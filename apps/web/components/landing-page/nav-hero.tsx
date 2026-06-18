// @ts-nocheck
"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { EASE_OUT_EXPO, Eyebrow, Icon, Star } from "./lib";
import { landingRoutes } from "./routes";
import { openLeadDialog } from "./lead-dialog";
import { scrollToSection } from "./scroll-to-section";
import { WaveMark } from "./wave-mark";

const useStateNH = useState,
  useEffectNH = useEffect,
  useRefNH = useRef;
const M = motion,
  AP = AnimatePresence;

/* ============================================================
   nav-hero.jsx — Navigation, Hero, Marquee strip
   ============================================================ */

/* ---------- WAVEFORM LOGO MARK ---------- */
/* WaveMark lives in ./wave-mark.tsx */

/* ---------- NAVIGATION ---------- */
const NAV_LINKS = [
  { label: "Features", id: "features" },
  { label: "How it Works", id: "how" },
  { label: "Pricing", id: "pricing" },
  { label: "Verticals", id: "verticals" },
  { label: "FAQ", id: "faq" },
];

function Nav() {
  const router = useRouter();
  const [scrolled, setScrolled] = useStateNH(false);
  const [menuOpen, setMenuOpen] = useStateNH(false);
  const [mobile, setMobile] = useStateNH(false);

  useEffectNH(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    const onResize = () => setMobile(window.innerWidth <= 900);
    onResize();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  useEffectNH(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
  }, [menuOpen]);

  const go = (id) => {
    setMenuOpen(false);
    scrollToSection(id, -70);
  };

  return (
    <M.nav
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        height: 64,
        transition: "background 300ms ease, box-shadow 300ms ease, border-color 300ms ease",
        background: scrolled ? "rgba(255,255,255,0.86)" : "rgba(255,255,255,0)",
        backdropFilter: scrolled ? "blur(20px) saturate(200%)" : "none",
        WebkitBackdropFilter: scrolled ? "blur(20px) saturate(200%)" : "none",
        borderBottom: `1px solid ${scrolled ? "#E8E3DE" : "transparent"}`,
        boxShadow: scrolled ? "0 1px 0 rgba(0,0,0,0.05)" : "none",
      }}
    >
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          height: 64,
          padding: mobile ? "0 24px" : "0 80px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* left */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <WaveMark />
          <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <span
              style={{ fontSize: 14, fontWeight: 700, letterSpacing: "-0.02em", color: "#111111" }}
            >
              AI Voice Agent
            </span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 500,
                letterSpacing: "0.04em",
                color: "#A09890",
                marginTop: -1,
              }}
            >
              by ZERQO
            </span>
          </div>
        </div>

        {/* center */}
        {!mobile && (
          <div style={{ display: "flex", gap: 4 }}>
            {NAV_LINKS.map((l) => (
              <button
                key={l.id}
                onClick={() => go(l.id)}
                style={{
                  border: "none",
                  background: "transparent",
                  fontSize: 14,
                  fontWeight: 500,
                  color: "#1C1C1C",
                  padding: "8px 14px",
                  borderRadius: 8,
                  cursor: "pointer",
                  transition: "all 150ms",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#F4F0EC";
                  e.currentTarget.style.color = "#0D0D0D";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "#1C1C1C";
                }}
              >
                {l.label}
              </button>
            ))}
          </div>
        )}

        {/* right */}
        {!mobile ? (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              style={{
                border: "none",
                background: "transparent",
                fontSize: 14,
                fontWeight: 500,
                color: "#6B6560",
                cursor: "pointer",
                transition: "color 150ms",
              }}
              onClick={() => router.push(landingRoutes.login)}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#111111")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#6B6560")}
            >
              Sign in
            </button>
            <M.button
              onClick={() => openLeadDialog("landing")}
              whileHover={{ scale: 1.03, backgroundColor: "#F04E00" }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              style={{
                background: "#111111",
                color: "#fff",
                fontSize: 13,
                fontWeight: 600,
                padding: "9px 20px",
                borderRadius: 100,
                border: "none",
                cursor: "pointer",
              }}
            >
              Get started
            </M.button>
          </div>
        ) : (
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Menu"
            style={{
              background: "transparent",
              border: "none",
              display: "flex",
              flexDirection: "column",
              gap: 4,
              cursor: "pointer",
              padding: 4,
            }}
          >
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                style={{ width: 20, height: 2, background: "#111111", borderRadius: 2 }}
              />
            ))}
          </button>
        )}
      </div>

      {/* mobile overlay */}
      <AP>
        {menuOpen && mobile && (
          <M.div
            key="mobile-menu"
            initial={{ y: "-100%", opacity: 0 }}
            animate={{ y: "0%", opacity: 1 }}
            exit={{ y: "-100%", opacity: 0 }}
            transition={{ duration: 0.3, ease: EASE_OUT_EXPO }}
            style={{
              position: "fixed",
              top: 64,
              left: 0,
              right: 0,
              background: "#fff",
              padding: 24,
              borderBottom: "1px solid #E8E3DE",
              boxShadow: "0 12px 32px rgba(0,0,0,0.08)",
            }}
          >
            {NAV_LINKS.map((l) => (
              <button
                key={l.id}
                onClick={() => go(l.id)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  border: "none",
                  borderBottom: "1px solid #F4F0EC",
                  background: "transparent",
                  fontSize: 18,
                  fontWeight: 500,
                  color: "#111",
                  padding: "14px 0",
                  cursor: "pointer",
                }}
              >
                {l.label}
              </button>
            ))}
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 18 }}>
              <button
                onClick={() => router.push(landingRoutes.login)}
                style={{
                  border: "1px solid #E8E3DE",
                  background: "#fff",
                  borderRadius: 100,
                  padding: "12px",
                  fontSize: 15,
                  fontWeight: 600,
                  color: "#111",
                  cursor: "pointer",
                }}
              >
                Sign in
              </button>
              <button
                onClick={() => openLeadDialog("landing")}
                style={{
                  border: "none",
                  background: "#F04E00",
                  color: "#fff",
                  borderRadius: 100,
                  padding: "12px",
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Get started
              </button>
            </div>
          </M.div>
        )}
      </AP>
    </M.nav>
  );
}

/* ---------- PHONE CALL MOCKUP ---------- */
function PhoneCall() {
  const bars = [0.35, 0.6, 1, 0.75, 0.45, 0.85, 0.55, 0.9, 0.4, 0.7, 1, 0.5, 0.8, 0.3];
  const ctlIcon = (d) => (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {d}
    </svg>
  );
  const Ctl = ({ children, label }) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 7 }}>
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: "50%",
          background: "rgba(255,255,255,0.08)",
          border: "1px solid rgba(255,255,255,0.07)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "rgba(255,255,255,0.85)",
        }}
      >
        {children}
      </div>
      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)" }}>{label}</span>
    </div>
  );
  return (
    <div style={{ position: "relative", width: "100%", maxWidth: 312, margin: "0 auto" }}>
      <div
        style={{
          borderRadius: 50,
          background: "#0A0A0A",
          padding: 9,
          boxShadow: "0 40px 80px -28px rgba(20,12,4,0.5), 0 0 0 1px rgba(0,0,0,0.04)",
        }}
      >
        <div
          style={{
            position: "relative",
            borderRadius: 42,
            overflow: "hidden",
            background: "linear-gradient(180deg,#1A1715 0%,#100D0C 60%)",
            aspectRatio: "9 / 19.2",
            display: "flex",
            flexDirection: "column",
            color: "#fff",
          }}
        >
          {/* notch */}
          <div
            style={{
              position: "absolute",
              top: 11,
              left: "50%",
              transform: "translateX(-50%)",
              width: 96,
              height: 26,
              background: "#0A0A0A",
              borderRadius: 18,
              zIndex: 3,
            }}
          />
          {/* status bar */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "15px 26px 0",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            <span style={{ fontFamily: "'Geist',sans-serif" }}>9:41</span>
            <span style={{ display: "inline-flex", gap: 4, alignItems: "center", opacity: 0.85 }}>
              <svg width="17" height="11" viewBox="0 0 17 11" fill="#fff">
                <rect x="0" y="7" width="3" height="4" rx="1" />
                <rect x="4.5" y="5" width="3" height="6" rx="1" />
                <rect x="9" y="2.5" width="3" height="8.5" rx="1" />
                <rect x="13.5" y="0" width="3" height="11" rx="1" />
              </svg>
              <svg width="22" height="11" viewBox="0 0 22 11" fill="none">
                <rect
                  x="0.5"
                  y="0.8"
                  width="18"
                  height="9.4"
                  rx="2.6"
                  stroke="#fff"
                  strokeOpacity="0.5"
                />
                <rect x="2" y="2.3" width="13.5" height="6.4" rx="1.4" fill="#fff" />
                <rect
                  x="19.6"
                  y="3.5"
                  width="1.6"
                  height="4"
                  rx="0.8"
                  fill="#fff"
                  fillOpacity="0.5"
                />
              </svg>
            </span>
          </div>

          {/* call body */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "4px 26px",
              textAlign: "center",
            }}
          >
            <div
              className="mono"
              style={{
                fontSize: 11,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "rgba(255,255,255,0.4)",
              }}
            >
              Incoming · Answered by AI
            </div>
            <div
              className="display"
              style={{ fontSize: 24, fontWeight: 600, marginTop: 8, letterSpacing: "-0.01em" }}
            >
              AI Voice Agent
            </div>
            <div className="mono" style={{ fontSize: 14, color: "#F04E00", marginTop: 6 }}>
              00:42
            </div>

            {/* avatar / waveform orb */}
            <div
              style={{
                position: "relative",
                marginTop: 22,
                width: 112,
                height: 112,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <M.div
                animate={{ scale: [1, 1.18, 1], opacity: [0.35, 0, 0.35] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: "easeOut" }}
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: "50%",
                  border: "1.5px solid #F04E00",
                }}
              />
              <div
                style={{
                  width: 112,
                  height: 112,
                  borderRadius: "50%",
                  background: "radial-gradient(circle at 38% 32%, #2A2320 0%, #15110F 75%)",
                  border: "1px solid rgba(240,78,0,0.25)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 3,
                }}
              >
                {bars.slice(0, 11).map((b, i) => (
                  <M.span
                    key={i}
                    style={{
                      width: 3,
                      height: 40,
                      borderRadius: 3,
                      background: "#F04E00",
                      transformOrigin: "center",
                    }}
                    animate={{ scaleY: [b * 0.4, b, b * 0.5] }}
                    transition={{
                      duration: 0.7 + (i % 4) * 0.18,
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: i * 0.05,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* live caption */}
            <div
              style={{
                marginTop: 20,
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 14,
                padding: "10px 14px",
                maxWidth: 240,
              }}
            >
              <div style={{ fontSize: 13, lineHeight: 1.45, color: "rgba(255,255,255,0.9)" }}>
                &ldquo;Booking confirmed for Monday, 2:00 PM with Dr.&nbsp;Sharma.&rdquo;
              </div>
            </div>
          </div>

          {/* controls */}
          <div style={{ padding: "0 32px 22px", flexShrink: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Ctl label="mute">
                {ctlIcon(
                  <>
                    <path d="M9 9V5a3 3 0 0 1 6 0v4" />
                    <path d="M5 10v1a7 7 0 0 0 14 0v-1M12 18v3" />
                  </>
                )}
              </Ctl>
              <Ctl label="keypad">
                {ctlIcon(
                  <>
                    <circle cx="6" cy="6" r="1" />
                    <circle cx="12" cy="6" r="1" />
                    <circle cx="18" cy="6" r="1" />
                    <circle cx="6" cy="12" r="1" />
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="18" cy="12" r="1" />
                    <circle cx="12" cy="18" r="1" />
                  </>
                )}
              </Ctl>
              <Ctl label="speaker">
                {ctlIcon(
                  <>
                    <path d="M4 9v6h4l5 4V5L8 9z" />
                    <path d="M16 9a3 3 0 0 1 0 6" />
                  </>
                )}
              </Ctl>
            </div>
            <div style={{ display: "flex", justifyContent: "center", marginTop: 14 }}>
              <div
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: "50%",
                  background: "#EF3B3B",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 8px 20px rgba(239,59,59,0.35)",
                }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#fff"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                >
                  <path
                    d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z"
                    transform="rotate(135 12 12)"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- FLOATING STAT CARDS ---------- */
function FloatCards({ mobile }) {
  if (mobile) return null;
  const cardSt = {
    position: "absolute",
    background: "#fff",
    border: "1px solid #E8E3DE",
    borderRadius: 14,
    padding: "12px 16px",
    boxShadow: "0 12px 30px -8px rgba(20,12,4,0.16)",
    zIndex: 10,
  };
  return (
    <>
      <M.div
        style={{ ...cardSt, bottom: 84, left: -28 }}
        animate={{ y: [0, -5, 0] }}
        transition={{ duration: 3.5, repeat: Infinity, delay: 0.5, ease: "easeInOut" }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: "#16A34A",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name="check" size={10} stroke="#fff" sw={2.5} />
          </span>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#16A34A" }}>
            Appointment booked
          </span>
        </div>
        <div style={{ fontSize: 11, color: "#6B6560", marginTop: 3 }}>
          Mon 3:00 PM · Priya Sharma
        </div>
      </M.div>

      <M.div
        style={{ ...cardSt, top: 96, right: -30, padding: "7px 13px", borderRadius: 100 }}
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      >
        <span style={{ fontSize: 11, fontWeight: 600, color: "#F04E00" }}>&lt; 1.2s response</span>
      </M.div>
    </>
  );
}

/* ---------- HERO ---------- */
function Hero() {
  const [mobile, setMobile] = useStateNH(false);
  useEffectNH(() => {
    const r = () => setMobile(window.innerWidth <= 900);
    r();
    window.addEventListener("resize", r);
    return () => window.removeEventListener("resize", r);
  }, []);

  const heroLine = (delay) => ({
    initial: { y: "110%" },
    animate: { y: "0%" },
    transition: { duration: 0.85, ease: EASE_OUT_EXPO, delay },
  });

  const grain = {
    position: "absolute",
    inset: 0,
    zIndex: 0,
    pointerEvents: "none",
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E")`,
    backgroundSize: "200px 200px",
    opacity: 0.025,
    mixBlendMode: "multiply",
  };

  const trust = ["No setup fee", "Cancel anytime", "Setup in 30 minutes"];

  return (
    <section
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        paddingTop: 64,
        background: "#fff",
      }}
    >
      <div style={grain} />
      <div
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: 1100,
          margin: "0 auto",
          padding: mobile ? "60px 24px" : "40px 80px",
          width: "100%",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: mobile ? "1fr" : "52% 48%",
            gap: mobile ? 40 : 60,
            alignItems: "center",
          }}
        >
          {/* LEFT */}
          <div style={{ textAlign: mobile ? "center" : "left" }}>
            <M.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: "#FFF4EE",
                border: "1px solid rgba(240,78,0,0.2)",
                borderRadius: 100,
                padding: "6px 14px 6px 8px",
                marginBottom: 22,
              }}
            >
              <span
                style={{
                  background: "#F04E00",
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: 100,
                  letterSpacing: "0.06em",
                }}
              >
                New
              </span>
              <span style={{ fontSize: 12, fontWeight: 500, color: "#6B6560" }}>
                Hindi language support coming in v2.0
              </span>
            </M.div>

            <M.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              style={{ display: mobile ? "flex" : "block", justifyContent: "center" }}
            >
              <Eyebrow text="AI Voice Agent by ZERQO" />
            </M.div>

            <h1
              className="display"
              style={{
                fontSize: "clamp(38px,8.5vw,86px)",
                fontWeight: 600,
                lineHeight: 0.98,
                letterSpacing: "-0.03em",
                color: "#111",
                margin: 0,
              }}
            >
              {[
                { t: <>Every call,</>, d: 0.2 },
                {
                  t: (
                    <>
                      every <span className="hl">customer,</span>
                    </>
                  ),
                  d: 0.28,
                },
                { t: <>answered.</>, d: 0.36 },
              ].map((ln, i) => (
                <span
                  key={i}
                  style={{ display: "block", overflow: "hidden", paddingBottom: "0.04em" }}
                >
                  <M.span style={{ display: "block" }} {...heroLine(ln.d)}>
                    {ln.t}
                  </M.span>
                </span>
              ))}
            </h1>

            <M.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.45 }}
              style={{
                fontSize: 18,
                fontWeight: 400,
                lineHeight: 1.72,
                color: "#6B6560",
                maxWidth: 460,
                marginTop: 24,
                marginLeft: mobile ? "auto" : 0,
                marginRight: mobile ? "auto" : 0,
              }}
            >
              Your AI voice receptionist takes every inbound call — booking appointments, answering
              questions, and handling customers — while you focus on running your business.
              Available 24/7. Zero missed calls. No extra staff.
            </M.p>

            <M.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              style={{
                display: "flex",
                gap: 16,
                alignItems: "center",
                marginTop: 22,
                flexWrap: "wrap",
                justifyContent: mobile ? "center" : "flex-start",
              }}
            >
              {trust.map((t, i) => (
                <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 16 }}>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      fontSize: 13,
                      color: "#6B6560",
                    }}
                  >
                    <Icon name="check" size={14} stroke="#16A34A" sw={2.2} />
                    {t}
                  </span>
                  {i < trust.length - 1 && (
                    <span style={{ width: 1, height: 14, background: "#E8E3DE" }} />
                  )}
                </span>
              ))}
            </M.div>

            <M.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.55 }}
              style={{
                display: "flex",
                flexDirection: mobile ? "column" : "row",
                gap: 12,
                alignItems: "center",
                marginTop: 28,
                flexWrap: "wrap",
                justifyContent: mobile ? "center" : "flex-start",
                width: mobile ? "100%" : "auto",
              }}
            >
              <M.button
                whileHover={{ scale: 1.02, backgroundColor: "#F04E00" }}
                whileTap={{ scale: 0.97 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
                onClick={() => openLeadDialog("landing")}
                style={{
                  background: "#111",
                  color: "#fff",
                  fontSize: 14,
                  fontWeight: 600,
                  padding: "15px 28px",
                  borderRadius: 100,
                  border: "none",
                  cursor: "pointer",
                  display: "block",
                  width: mobile ? "100%" : "auto",
                  maxWidth: 360,
                }}
              >
                Get started
              </M.button>
              <M.button
                whileHover={{ y: 0 }}
                className="demo-btn"
                style={{
                  background: "#fff",
                  border: "1px solid #E8E3DE",
                  color: "#111",
                  fontSize: 14,
                  fontWeight: 600,
                  padding: "14px 24px",
                  borderRadius: 100,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 6,
                  transition: "all 180ms",
                  width: mobile ? "100%" : "auto",
                  maxWidth: 360,
                }}
                onClick={() => scrollToSection("features", -70)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "#C8C3BE";
                  e.currentTarget.style.background = "#F8F5F1";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#E8E3DE";
                  e.currentTarget.style.background = "#fff";
                }}
              >
                Watch demo call{" "}
                <M.span style={{ display: "inline-block" }} whileHover={{ x: 3 }}>
                  ↗
                </M.span>
              </M.button>
            </M.div>
          </div>

          {/* RIGHT */}
          <M.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1.2, delay: 0.3, ease: EASE_OUT_EXPO }}
            style={{
              position: "relative",
              width: mobile ? "85%" : "100%",
              margin: mobile ? "0 auto" : 0,
            }}
          >
            <PhoneCall />
            <FloatCards mobile={mobile} />
          </M.div>
        </div>
      </div>
    </section>
  );
}

/* ---------- MARQUEE ---------- */
function Marquee() {
  const items = [
    "Clinics",
    "Restaurants",
    "Hotels",
    "Dental Practices",
    "Pharmacies",
    "Retail Stores",
    "Salons",
    "Gyms",
    "Guest Houses",
    "Optical Stores",
    "Pathology Labs",
    "Veterinary Clinics",
  ];
  const Row = () => (
    <span style={{ display: "inline-flex", alignItems: "center", flexShrink: 0 }}>
      {items.map((it, i) => (
        <span
          key={i}
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "#A09890",
            letterSpacing: "0.02em",
            whiteSpace: "nowrap",
          }}
        >
          {it}
          <span style={{ color: "#F04E00", margin: "0 16px" }}>·</span>
        </span>
      ))}
    </span>
  );
  return (
    <div
      style={{
        background: "#F8F5F1",
        borderTop: "1px solid #E8E3DE",
        borderBottom: "1px solid #E8E3DE",
        padding: "14px 0",
        overflow: "hidden",
      }}
    >
      <M.div
        style={{ display: "flex", width: "max-content" }}
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
      >
        <Row />
        <Row />
      </M.div>
    </div>
  );
}

export { Nav, Hero, Marquee };
