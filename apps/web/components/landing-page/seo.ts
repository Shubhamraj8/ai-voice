import type { Metadata } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const landingPageMetadata: Metadata = {
  title: "AI Voice Agent by ZERQO — Every call answered",
  description:
    "Your AI voice receptionist takes every inbound call — booking appointments, answering questions, and handling customers 24/7. Built for Indian SMBs.",
  metadataBase: new URL(siteUrl),
  openGraph: {
    title: "AI Voice Agent by ZERQO — Every call answered",
    description:
      "AI phone agents for clinics, restaurants, hotels, and more. Zero missed calls. Start your 7-day free trial.",
    url: siteUrl,
    siteName: "AI Voice Agent by ZERQO",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Voice Agent by ZERQO — Every call answered",
    description: "AI phone agents for Indian SMBs — 24/7 booking, FAQs, and human handoff.",
  },
};
