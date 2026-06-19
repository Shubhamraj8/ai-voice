"use client";

import { useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { requestDataExport } from "@/lib/api/portal";

type Status = "idle" | "requesting" | "done" | "error";

export function DataExportCard() {
  const [status, setStatus] = useState<Status>("idle");

  const onRequest = async () => {
    setStatus("requesting");
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      setStatus("error");
      return;
    }

    const ok = await requestDataExport(session.access_token);
    setStatus(ok ? "done" : "error");
  };

  return (
    <div className="rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">Export your data</h2>
      <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-zerqo-muted">
        Download everything we hold for your workspace — calls, transcripts, knowledge documents,
        billing history, and your activity log. We&rsquo;ll email you a secure download link that
        works for 7 days.
      </p>

      {status === "done" ? (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13px] text-emerald-800">
          Your export has started. We&rsquo;ll email a download link to your account shortly.
        </div>
      ) : null}
      {status === "error" ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          Something went wrong starting your export. Please try again.
        </div>
      ) : null}

      <button
        type="button"
        onClick={onRequest}
        disabled={status === "requesting"}
        className="mt-4 inline-flex items-center gap-2 rounded-xl bg-zerqo-orange px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-zerqo-orange/90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "requesting" ? (
          <>
            <Loader2 className="size-4 animate-spin" /> Starting export…
          </>
        ) : (
          <>
            <Download className="size-4" /> Request data export
          </>
        )}
      </button>
    </div>
  );
}
