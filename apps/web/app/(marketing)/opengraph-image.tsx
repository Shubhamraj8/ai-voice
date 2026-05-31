import { ImageResponse } from "next/og";

export const runtime = "edge";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "AI Voice Agent by ZERQO — Every call answered";

export default function LandingOpenGraphImage() {
  return new ImageResponse(
    <div
      style={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "80px",
        background: "linear-gradient(135deg, #0d0d0d 0%, #1e293b 100%)",
        color: "white",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ fontSize: 28, opacity: 0.7, marginBottom: 16 }}>by ZERQO</div>
      <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.05, maxWidth: 900 }}>
        Every call, every customer, answered.
      </div>
      <div style={{ fontSize: 26, marginTop: 28, opacity: 0.85, maxWidth: 800 }}>
        AI phone agents for Indian SMBs — 24/7 booking, FAQs, and human handoff.
      </div>
    </div>,
    { ...size }
  );
}
