"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api/config";

const EVENT = "zerqo:open-lead";

/** Open the lead-capture dialog from any landing CTA. */
export function openLeadDialog(source = "landing") {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(EVENT, { detail: { source } }));
}

type Form = {
  business_name: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  message: string;
};

const EMPTY: Form = {
  business_name: "",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  message: "",
};

const FIELDS: { key: keyof Form; label: string; type?: string; required?: boolean }[] = [
  { key: "business_name", label: "Business name" },
  { key: "contact_name", label: "Your name" },
  { key: "contact_email", label: "Work email", type: "email", required: true },
  { key: "contact_phone", label: "Phone", type: "tel" },
];

export function LeadDialog() {
  const [open, setOpen] = useState(false);
  const [source, setSource] = useState("landing");
  const [form, setForm] = useState<Form>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as { source?: string } | undefined;
      setSource(detail?.source ?? "landing");
      setForm(EMPTY);
      setDone(false);
      setError(null);
      setOpen(true);
    };
    window.addEventListener(EVENT, handler);
    return () => window.removeEventListener(EVENT, handler);
  }, []);

  if (!open) return null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const resp = await fetch(`${getApiBaseUrl()}/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, source }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body?.detail?.message ?? "Something went wrong. Please try again.");
      }
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 10,
    border: "1px solid #E8E3DE",
    fontSize: 14,
    outline: "none",
    background: "#fff",
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
    >
      <button
        aria-label="Close"
        onClick={() => setOpen(false)}
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(17,17,17,0.45)",
          border: "none",
          cursor: "pointer",
        }}
      />
      <div
        style={{
          position: "relative",
          zIndex: 1,
          width: "100%",
          maxWidth: 460,
          background: "#FAF7F3",
          borderRadius: 20,
          padding: 28,
          boxShadow: "0 24px 70px -20px rgba(0,0,0,0.45)",
        }}
      >
        <button
          aria-label="Close"
          onClick={() => setOpen(false)}
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            background: "transparent",
            border: "none",
            fontSize: 22,
            lineHeight: 1,
            color: "#6B6560",
            cursor: "pointer",
          }}
        >
          ×
        </button>

        {done ? (
          <div style={{ textAlign: "center", padding: "16px 4px" }}>
            <div style={{ fontSize: 40 }}>✅</div>
            <h3 style={{ fontSize: 20, fontWeight: 600, margin: "12px 0 6px", color: "#111" }}>
              Thanks — we’ll be in touch!
            </h3>
            <p style={{ fontSize: 14, color: "#6B6560", lineHeight: 1.6 }}>
              Our team will email you shortly with plans and next steps.
            </p>
            <button
              onClick={() => setOpen(false)}
              style={{
                marginTop: 18,
                padding: "10px 22px",
                borderRadius: 100,
                background: "#111",
                color: "#fff",
                border: "none",
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={submit}>
            <h3 style={{ fontSize: 22, fontWeight: 600, margin: "0 0 4px", color: "#111" }}>
              Get started
            </h3>
            <p style={{ fontSize: 14, color: "#6B6560", margin: "0 0 18px", lineHeight: 1.6 }}>
              Tell us about your business — we’ll email you the right plan and set you up.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {FIELDS.map((f) => (
                <div key={f.key}>
                  <label
                    style={{ fontSize: 13, color: "#6B6560", display: "block", marginBottom: 4 }}
                  >
                    {f.label}
                    {f.required ? " *" : ""}
                  </label>
                  <input
                    type={f.type ?? "text"}
                    required={f.required}
                    value={form[f.key]}
                    onChange={(e) => setForm((s) => ({ ...s, [f.key]: e.target.value }))}
                    style={inputStyle}
                  />
                </div>
              ))}
              <div>
                <label
                  style={{ fontSize: 13, color: "#6B6560", display: "block", marginBottom: 4 }}
                >
                  Anything else?
                </label>
                <textarea
                  rows={3}
                  value={form.message}
                  onChange={(e) => setForm((s) => ({ ...s, message: e.target.value }))}
                  style={{ ...inputStyle, resize: "vertical" }}
                />
              </div>
            </div>

            {error ? (
              <p style={{ fontSize: 13, color: "#DC2626", marginTop: 12 }}>{error}</p>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              style={{
                marginTop: 18,
                width: "100%",
                padding: "12px 22px",
                borderRadius: 100,
                background: "#F04E00",
                color: "#fff",
                border: "none",
                fontSize: 15,
                fontWeight: 600,
                cursor: submitting ? "default" : "pointer",
                opacity: submitting ? 0.7 : 1,
              }}
            >
              {submitting ? "Sending…" : "Request access"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
