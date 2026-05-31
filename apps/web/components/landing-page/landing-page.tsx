"use client";

import { useEffect } from "react";
import { CTABanner, Footer, ScrollProgress } from "./cta-footer";
import { FAQ, Pricing } from "./pricing-faq";
import { HowItWorks, Stats, ValueProp } from "./mid";
import { Hero, Marquee, Nav } from "./nav-hero";
import { DarkShowcase, Verticals } from "./verticals-dark";
import "./index.css";

type LenisInstance = {
  raf: (time: number) => void;
  scrollTo: (target: Element | string | number, opts?: { offset?: number }) => void;
  destroy: () => void;
};

declare global {
  interface Window {
    __lenis?: LenisInstance;
  }
}

export function LandingPage() {
  useEffect(() => {
    let rafId = 0;
    let lenis: LenisInstance | undefined;

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/@studio-freight/lenis@1.0.42/dist/lenis.min.js";
    script.onload = () => {
      const LenisCtor = (window as Window & { Lenis?: new (opts: object) => LenisInstance }).Lenis;
      if (!LenisCtor) return;
      lenis = new LenisCtor({
        duration: 1.4,
        easing: (t: number) => Math.min(1, 1.001 - 2 ** (-10 * t)),
        smooth: true,
        smoothTouch: false,
      });
      window.__lenis = lenis;
      const raf = (time: number) => {
        lenis?.raf(time);
        rafId = requestAnimationFrame(raf);
      };
      rafId = requestAnimationFrame(raf);
    };
    document.head.appendChild(script);

    return () => {
      cancelAnimationFrame(rafId);
      lenis?.destroy();
      delete window.__lenis;
      script.remove();
    };
  }, []);

  return (
    <div className="landing-page-root">
      <ScrollProgress />
      <Nav />
      <Hero />
      <Marquee />
      <ValueProp />
      <Stats />
      <HowItWorks />
      <Verticals />
      <DarkShowcase />
      <Pricing />
      <FAQ />
      <CTABanner />
      <Footer />
    </div>
  );
}
