// @ts-nocheck
"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FadeUp, EyebrowWhite, Icon } from "./lib";
import { useMobile } from "./mid";
import { WaveMark } from "./wave-mark";
import { openLeadDialog } from "./lead-dialog";

const useS5 = useState,
  useE5 = useEffect;
const M5 = motion;

/* ============================================================
   cta-footer.jsx — CTA banner, Footer, Scroll progress
   ============================================================ */

/* ---------- SCROLL PROGRESS ---------- */
function ScrollProgress() {
  const [p, setP] = useS5(0);
  useE5(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const h = document.documentElement.scrollHeight - window.innerHeight;
        setP(h > 0 ? window.scrollY / h : 0);
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    onScroll();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 2,
        zIndex: 200,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          height: "100%",
          width: "100%",
          background: "#F04E00",
          transform: `scaleX(${p})`,
          transformOrigin: "left",
          transition: "transform 80ms linear",
        }}
      />
    </div>
  );
}

/* ---------- CTA BANNER ---------- */
function CTABanner() {
  const mobile = useMobile();
  return (
    <section style={{ background: "#0D0D0D", position: "relative", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
          width: 800,
          height: 400,
          background:
            "radial-gradient(ellipse 800px 400px at center, rgba(240,78,0,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "relative",
          maxWidth: 700,
          margin: "0 auto",
          textAlign: "center",
          padding: mobile ? "80px 24px" : "96px 80px",
        }}
      >
        <FadeUp>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <EyebrowWhite text="Get started today" />
          </div>
          <h2
            className="display"
            style={{
              fontSize: "clamp(36px,4.8vw,58px)",
              fontWeight: 600,
              lineHeight: 1.05,
              letterSpacing: "-0.022em",
              color: "#fff",
              margin: 0,
              textWrap: "balance",
              maxWidth: 640,
              marginLeft: "auto",
              marginRight: "auto",
            }}
          >
            Every missed call is a missed{" "}
            <span style={{ color: "#F04E00", whiteSpace: "nowrap" }}>₹14,000.</span>
          </h2>
          <p
            style={{
              fontSize: 17,
              color: "rgba(255,255,255,0.5)",
              lineHeight: 1.72,
              maxWidth: 520,
              margin: "16px auto 0",
            }}
          >
            The average Indian clinic loses ₹14,000 in revenue per week from missed appointment
            calls. ZERQO pays for itself in 6 days.
          </p>
          <div
            style={{
              display: "flex",
              gap: 12,
              justifyContent: "center",
              marginTop: 32,
              flexWrap: "wrap",
            }}
          >
            <M5.button
              onClick={() => openLeadDialog("cta-footer")}
              whileHover={{ scale: 1.03, backgroundColor: "#FF5E14" }}
              whileTap={{ scale: 0.97 }}
              transition={{ duration: 0.18 }}
              style={{
                background: "#F04E00",
                color: "#fff",
                padding: "15px 32px",
                borderRadius: 100,
                fontSize: 14,
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                boxShadow: "0 14px 34px -10px rgba(240,78,0,0.6)",
              }}
            >
              Get started
            </M5.button>
            <button
              style={{
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "rgba(255,255,255,0.7)",
                padding: "14px 24px",
                borderRadius: 100,
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 180ms",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.35)";
                e.currentTarget.style.color = "#fff";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)";
                e.currentTarget.style.color = "rgba(255,255,255,0.7)";
              }}
            >
              Talk to sales →
            </button>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}

/* ---------- FOOTER ---------- */
const FOOTER_COLS = [
  {
    h: "Product",
    links: ["Overview", "Features", "Pricing", "Integrations", "Security", "Status"],
  },
  { h: "Verticals", links: ["Clinics", "Restaurants", "Hotels", "Retail", "Salons", "Pharmacies"] },
  {
    h: "Developers",
    links: ["Documentation", "API Reference", "Webhooks", "Quickstart", "Status"],
  },
  { h: "Company", links: ["About ZERQO", "Blog", "Careers", "Privacy Policy", "Terms of Service"] },
];

const SocialIcon = ({ name }) => {
  const p = {
    x: <path d="M4 4l16 16M20 4L4 20" />,
    instagram: (
      <>
        <rect x="4" y="4" width="16" height="16" rx="5" />
        <circle cx="12" cy="12" r="3.5" />
        <circle cx="17" cy="7" r="1" fill="currentColor" stroke="none" />
      </>
    ),
    youtube: (
      <>
        <rect x="3" y="6" width="18" height="12" rx="3" />
        <path d="M11 9.5l4 2.5-4 2.5z" fill="currentColor" stroke="none" />
      </>
    ),
    tiktok: <path d="M14 4v9.5a3.5 3.5 0 1 1-3-3.46M14 7c.8 1.4 2.2 2.3 4 2.4" />,
  };
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {p[name]}
    </svg>
  );
};

function Footer() {
  const mobile = useMobile();
  return (
    <footer style={{ background: "#0F0F0F", position: "relative", overflow: "hidden" }}>
      <M5.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.5, duration: 1.2 }}
        style={{
          position: "absolute",
          bottom: 0,
          left: "50%",
          transform: "translateX(-50%)",
          fontSize: mobile ? 80 : "clamp(120px,18vw,240px)",
          fontWeight: 900,
          letterSpacing: "-0.05em",
          color: "rgba(255,255,255,0.025)",
          userSelect: "none",
          pointerEvents: "none",
          whiteSpace: "nowrap",
          lineHeight: 1,
        }}
      >
        ZERQO
      </M5.div>

      <div
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: 1100,
          margin: "0 auto",
          padding: mobile ? "0 24px" : "0 80px",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: mobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: mobile ? 40 : 48,
            paddingTop: 64,
            paddingBottom: 48,
            borderBottom: "1px solid #1E1E1E",
          }}
        >
          {/* left */}
          <div style={{ maxWidth: 280 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <WaveMark dark />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span
                  style={{ fontSize: 14, fontWeight: 700, letterSpacing: "-0.02em", color: "#fff" }}
                >
                  AI Voice Agent
                </span>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 500,
                    letterSpacing: "0.04em",
                    color: "#5A5654",
                    marginTop: -1,
                  }}
                >
                  by ZERQO
                </span>
              </div>
            </div>
            <p style={{ fontSize: 13, color: "#5A5654", lineHeight: 1.65, marginTop: 14 }}>
              For businesses that want every customer call answered perfectly.
            </p>
            <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
              {["tiktok", "x", "instagram", "youtube"].map((s) => (
                <a
                  key={s}
                  href="#"
                  onClick={(e) => e.preventDefault()}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 8,
                    background: "#1A1A1A",
                    border: "1px solid #2A2826",
                    color: "#5A5654",
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 150ms",
                    textDecoration: "none",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "#222";
                    e.currentTarget.style.borderColor = "#3A3836";
                    e.currentTarget.style.color = "#fff";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "#1A1A1A";
                    e.currentTarget.style.borderColor = "#2A2826";
                    e.currentTarget.style.color = "#5A5654";
                  }}
                >
                  <SocialIcon name={s} />
                </a>
              ))}
            </div>
          </div>
          {/* link cols */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: mobile ? "1fr 1fr" : "repeat(4,auto)",
              gap: mobile ? "32px 24px" : 48,
            }}
          >
            {FOOTER_COLS.map((col) => (
              <div key={col.h}>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "#3A3836",
                    marginBottom: 16,
                  }}
                >
                  {col.h}
                </div>
                {col.links.map((l) => (
                  <a
                    key={l}
                    href="#"
                    onClick={(e) => e.preventDefault()}
                    style={{
                      display: "block",
                      fontSize: 13,
                      color: "#5A5654",
                      marginBottom: 10,
                      textDecoration: "none",
                      transition: "color 150ms",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")}
                    onMouseLeave={(e) => (e.currentTarget.style.color = "#5A5654")}
                  >
                    {l}
                  </a>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: mobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "20px 0",
            gap: 8,
            textAlign: "center",
          }}
        >
          <span style={{ fontSize: 12, color: "#3A3836" }}>© 2026 ZERQO. All rights reserved.</span>
          <span style={{ fontSize: 12, color: "#3A3836" }}>
            AI Voice Agent is a product of <span style={{ color: "#5A5654" }}>ZERQO</span>
          </span>
          <span style={{ fontSize: 12, color: "#3A3836" }}>Built in India</span>
        </div>
      </div>
    </footer>
  );
}

export { ScrollProgress, CTABanner, Footer };
