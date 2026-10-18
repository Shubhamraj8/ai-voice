"use client";

import { useState } from "react";
import { Loader2, PhoneCall } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { requestOutboundCall } from "@/lib/api/portal";

type Status = "idle" | "calling" | "done" | "error";

export function OutboundCallCard() {
  const [number, setNumber] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  const onCall = async () => {
    let to = number.trim().replace(/[\s()-]/g, "");
    if (!to) return;
    if (/^\d{10}$/.test(to)) {
      to = `+91${to}`;
    } else if (!to.startsWith("+")) {
      to = `+${to}`;
    }

    setStatus("calling");
    setError(null);

    const supabase = createClient();
    let {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      const refreshed = await supabase.auth.refreshSession();
      session = refreshed.data.session;
    } else {
      try {
        const parts = session.access_token.split(".");
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1]));
          if (typeof payload.exp === "number" && payload.exp * 1000 <= Date.now() + 30000) {
            const refreshed = await supabase.auth.refreshSession();
            if (refreshed.data.session) {
              session = refreshed.data.session;
            }
          }
        }
      } catch {
        // ignore parse error
      }
    }

    if (!session?.access_token) {
      setStatus("error");
      setError("Your session expired — please refresh.");
      return;
    }

    const result = await requestOutboundCall(session.access_token, to);
    if (result.ok) {
      setStatus("done");
    } else {
      setStatus("error");
      setError(result.error ?? "Call failed");
    }
  };

  const isTrialError =
    error?.toLowerCase().includes("trial") || error?.toLowerCase().includes("unverified");

  return (
    <div className="rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm">
      <div className="mb-2 flex items-center gap-2 text-zerqo-muted">
        <PhoneCall className="size-4" />
        <span className="text-[13px] font-semibold">Place a call</span>
      </div>
      <p className="text-[13px] leading-relaxed text-zerqo-muted">
        Have your agent call a phone number. The answered call runs your agent (with its knowledge
        base) just like an inbound call.
      </p>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <input
          type="tel"
          inputMode="tel"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
          placeholder="+9198XXXXXXXX"
          className="flex-1 rounded-xl border border-zerqo-line bg-white px-3 py-2.5 text-sm text-zerqo-ink outline-none placeholder:text-zerqo-muted focus:border-zerqo-orange"
        />
        <button
          type="button"
          onClick={onCall}
          disabled={status === "calling" || !number.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-zerqo-orange px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-zerqo-orange/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {status === "calling" ? (
            <>
              <Loader2 className="size-4 animate-spin" /> Calling…
            </>
          ) : (
            <>
              <PhoneCall className="size-4" /> Call now
            </>
          )}
        </button>
      </div>

      <p className="mt-2 text-xs text-zerqo-muted">
        Format: <span className="font-mono text-zerqo-ink">+91XXXXXXXXXX</span>. Note: Twilio trial
        accounts require recipient numbers to be verified first.
      </p>

      {status === "done" ? (
        <p className="mt-3 text-[13px] text-emerald-700">
          Calling now — your phone should ring shortly.
        </p>
      ) : null}
      {status === "error" && error ? (
        <div className="mt-3 rounded-xl border border-red-200 bg-red-50/80 p-3.5 text-[13px] text-red-800">
          <p className="font-medium">{error}</p>
          {isTrialError ? (
            <p className="mt-1.5 text-xs text-red-700">
              💡 <strong>Twilio Trial restriction:</strong> To receive calls in trial mode, add your
              phone number to{" "}
              <a
                href="https://console.twilio.com/us1/develop/phone-numbers/manage/verified"
                target="_blank"
                rel="noreferrer"
                className="underline font-semibold hover:text-red-900"
              >
                Twilio Console → Verified Caller IDs
              </a>
              , or upgrade your Twilio account.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
