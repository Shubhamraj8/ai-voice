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
    const to = number.trim();
    if (!to) return;
    setStatus("calling");
    setError(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
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

      {status === "done" ? (
        <p className="mt-3 text-[13px] text-emerald-700">
          Calling now — your phone should ring shortly.
        </p>
      ) : null}
      {status === "error" && error ? (
        <p className="mt-3 text-[13px] text-red-700">{error}</p>
      ) : null}
    </div>
  );
}
