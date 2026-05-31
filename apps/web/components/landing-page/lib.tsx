// @ts-nocheck
"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";

/* ============================================================
   lib.jsx — design tokens, reusable animation components, icons
   ============================================================ */

const EASE_OUT_EXPO = [0.16, 1, 0.3, 1];

/* ---- color tokens ---- */
const C = {
  orange: "#F04E00",
  orangeHover: "#D94200",
  orangeLight: "#FFF4EE",
  orangeGlow: "rgba(240,78,0,0.10)",
  orangeGlowMd: "rgba(240,78,0,0.18)",
  black: "#0D0D0D",
  g900: "#111111",
  g800: "#1C1C1C",
  g600: "#6B6560",
  g400: "#A09890",
  g200: "#E8E3DE",
  g100: "#F4F0EC",
  g50: "#F8F5F1",
  white: "#FFFFFF",
  darkBg: "#0D0D0D",
  darkSurface: "#161616",
  darkSurface2: "#1E1E1E",
  darkBorder: "#2A2826",
  darkText: "#FFFFFF",
  darkMuted: "#7A7370",
  green: "#16A34A",
  redDot: "#F05252",
  yellowDot: "#F0B429",
};

/* ---- card base (shared inline style + hover handled by motion) ---- */
const cardBase = {
  background: "#FFFFFF",
  border: "1px solid #E8E3DE",
  borderRadius: "16px",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03)",
};

/* ---- FadeUp ---- */
const FadeUp = ({ children, delay = 0, className = "", style = {} }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.12 });
  return (
    <motion.div
      ref={ref}
      className={className}
      style={style}
      initial={{ opacity: 0, y: 30 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.85, ease: EASE_OUT_EXPO, delay }}
    >
      {children}
    </motion.div>
  );
};

/* ---- FadeIn ---- */
const FadeIn = ({ children, delay = 0, className = "", style = {} }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.1 });
  return (
    <motion.div
      ref={ref}
      className={className}
      style={style}
      initial={{ opacity: 0 }}
      animate={inView ? { opacity: 1 } : {}}
      transition={{ duration: 0.9, ease: "easeOut", delay }}
    >
      {children}
    </motion.div>
  );
};

/* ---- Stagger container ---- */
const Stagger = ({ children, className = "", style = {}, delay = 0 }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.08 });
  return (
    <motion.div
      ref={ref}
      className={className}
      style={style}
      initial="hidden"
      animate={inView ? "show" : "hidden"}
      variants={{ show: { transition: { staggerChildren: 0.09, delayChildren: delay } } }}
    >
      {children}
    </motion.div>
  );
};

/* ---- Stagger item ---- */
const SI = ({ children, className = "", style = {} }) => (
  <motion.div
    className={className}
    style={style}
    variants={{
      hidden: { opacity: 0, y: 24 },
      show: { opacity: 1, y: 0, transition: { duration: 0.75, ease: EASE_OUT_EXPO } },
    }}
  >
    {children}
  </motion.div>
);

/* ---- CountUp ---- */
const CountUp = ({ end, prefix = "", suffix = "", duration = 2200 }) => {
  const [val, setVal] = useState(0);
  const containerRef = useRef(null);
  const inView = useInView(containerRef, { once: true, amount: 0.2 });
  const formatVal = (raw) => {
    const display = typeof raw === "number" && raw >= 1000 ? raw.toLocaleString("en-IN") : raw;
    return `${prefix}${display}${suffix}`;
  };
  const finalText = formatVal(end);

  useEffect(() => {
    if (!inView) return;

    let rafId = 0;
    let cancelled = false;
    const startTime = performance.now();
    const isDecimal = String(end).includes(".");

    const step = (now) => {
      if (cancelled) return;
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      const current = isDecimal ? parseFloat((eased * end).toFixed(1)) : Math.floor(eased * end);
      setVal(progress < 1 ? current : end);
      if (progress < 1) rafId = requestAnimationFrame(step);
    };

    setVal(0);
    rafId = requestAnimationFrame(step);
    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
    };
  }, [inView, end, duration]);

  return (
    <span
      ref={containerRef}
      style={{
        display: "inline-grid",
        fontVariantNumeric: "tabular-nums",
      }}
    >
      <span
        style={{ gridArea: "1 / 1", visibility: "hidden", pointerEvents: "none" }}
        aria-hidden="true"
      >
        {finalText}
      </span>
      <span style={{ gridArea: "1 / 1" }}>{formatVal(val)}</span>
    </span>
  );
};

/* ---- Eyebrow (editorial mono label) ---- */
const Eyebrow = ({ text, dark = false }) => (
  <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 22 }}>
    <span
      style={{
        width: 22,
        height: 2,
        background: dark ? "rgba(240,78,0,0.9)" : "#F04E00",
        flexShrink: 0,
      }}
    />
    <span
      className="mono"
      style={{
        fontSize: 12,
        fontWeight: 500,
        letterSpacing: "0.02em",
        color: dark ? "rgba(255,255,255,0.55)" : "#6B6560",
      }}
    >
      {text}
    </span>
  </div>
);

/* ---- Eyebrow on dark CTA ---- */
const EyebrowWhite = ({ text }) => (
  <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 22 }}>
    <span style={{ width: 22, height: 2, background: "rgba(255,255,255,0.4)", flexShrink: 0 }} />
    <span
      className="mono"
      style={{
        fontSize: 12,
        fontWeight: 500,
        letterSpacing: "0.02em",
        color: "rgba(255,255,255,0.5)",
      }}
    >
      {text}
    </span>
  </div>
);

/* ---- editorial heading with animated underline on the highlight word ---- */
const Heading2 = ({ children, style = {}, className = "" }) => (
  <h2
    className={className}
    style={{
      fontSize: "clamp(36px,4.6vw,56px)",
      fontWeight: 600,
      lineHeight: 1.04,
      letterSpacing: "-0.022em",
      color: "#111111",
      margin: 0,
      textWrap: "balance",
      ...style,
    }}
  >
    {children}
  </h2>
);

/* ============================================================
   ICON SET — all inline SVG, strokeWidth 1.75, round caps
   ============================================================ */
const Icon = ({ name, size = 18, stroke = "currentColor", sw = 1.75, fill = "none" }) => {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill,
    stroke,
    strokeWidth: sw,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };
  const paths = {
    phone: (
      <>
        <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z" />
      </>
    ),
    calendar: (
      <>
        <rect x="3" y="4.5" width="18" height="16" rx="2.5" />
        <path d="M3 9h18M8 2.5v4M16 2.5v4" />
        <path d="M7.5 13h2M11 13h2M14.5 13h2M7.5 16.5h2M11 16.5h2" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V4M12 4 7.5 8.5M12 4l4.5 4.5" />
        <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
      </>
    ),
    transfer: (
      <>
        <path d="M4 8h13M13 4l4 4-4 4" />
        <path d="M20 16H7M11 12l-4 4 4 4" />
      </>
    ),
    check: (
      <>
        <path d="M5 12.5 10 17 19 7" />
      </>
    ),
    medical: (
      <>
        <path d="M3 12h4l2-5 3 11 2.5-6H21" />
      </>
    ),
    food: (
      <>
        <path d="M5 3v8a3 3 0 0 0 6 0V3M8 3v18M19 3c-1.5 0-2.5 2-2.5 5v4h2.5M19 12v9" />
      </>
    ),
    bed: (
      <>
        <path d="M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 14h18M3 18v2M21 18v2M7 10V7a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v3" />
      </>
    ),
    cart: (
      <>
        <circle cx="9" cy="20" r="1.4" />
        <circle cx="18" cy="20" r="1.4" />
        <path d="M2 3h3l2.2 12.2a2 2 0 0 0 2 1.6h8a2 2 0 0 0 2-1.6L22 7H6" />
      </>
    ),
    scissors: (
      <>
        <circle cx="6" cy="6" r="2.5" />
        <circle cx="6" cy="18" r="2.5" />
        <path d="M8 7.5 20 18M8 16.5 20 6M9.5 12 14 9" />
      </>
    ),
    pill: (
      <>
        <rect x="3" y="9" width="18" height="6" rx="3" transform="rotate(45 12 12)" />
        <path d="M9 9 15 15" />
      </>
    ),
    cloud: (
      <>
        <path d="M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17 9.5a3.5 3.5 0 0 1 .5 6.97" />
        <path d="M12 13v5M12 13l-2.2 2.2M12 13l2.2 2.2" />
      </>
    ),
    pdf: (
      <>
        <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
        <path d="M14 3v5h5" />
      </>
    ),
    link: (
      <>
        <path d="M10 13a4 4 0 0 0 5.66 0l3-3a4 4 0 1 0-5.66-5.66l-1.5 1.5" />
        <path d="M14 11a4 4 0 0 0-5.66 0l-3 3a4 4 0 1 0 5.66 5.66l1.5-1.5" />
      </>
    ),
    sms: (
      <>
        <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4L3 21l1.1-3.3A8.4 8.4 0 1 1 21 11.5Z" />
        <path d="M8 11h.01M12 11h.01M16 11h.01" />
      </>
    ),
    slider: (
      <>
        <path d="M4 8h10M18 8h2M4 16h2M10 16h10" />
        <circle cx="16" cy="8" r="2.2" fill={fill} />
        <circle cx="8" cy="16" r="2.2" fill={fill} />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z" />
        <path d="M9 12l2 2 4-4" />
      </>
    ),
    brain: (
      <>
        <path d="M12 5v14M12 9l-3-3M12 9l3-3M12 14l-3 3M12 14l3 3" />
        <circle cx="12" cy="9" r="1" fill={stroke} />
        <circle cx="9" cy="6" r="1" fill={stroke} />
        <circle cx="15" cy="6" r="1" fill={stroke} />
      </>
    ),
    lock: (
      <>
        <rect x="5" y="11" width="14" height="9" rx="2" />
        <path d="M8 11V8a4 4 0 0 1 8 0v3" />
      </>
    ),
    building: (
      <>
        <rect x="5" y="3" width="14" height="18" rx="1.5" />
        <path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2M10 21v-3h4v3" />
      </>
    ),
    arrow: (
      <>
        <path d="M5 12h14M13 6l6 6-6 6" />
      </>
    ),
  };
  return <svg {...common}>{paths[name]}</svg>;
};

/* ---- Star (filled) ---- */
const Star = ({ size = 12, color = "#F04E00" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
  </svg>
);

export {
  EASE_OUT_EXPO,
  C,
  cardBase,
  FadeUp,
  FadeIn,
  Stagger,
  SI,
  CountUp,
  Eyebrow,
  EyebrowWhite,
  Heading2,
  Icon,
  Star,
};
