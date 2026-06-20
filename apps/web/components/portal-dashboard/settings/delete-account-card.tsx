"use client";

import { useState } from "react";
import { Loader2, Trash2 } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { requestAccountDeletion } from "@/lib/api/portal";

type Status = "idle" | "requesting" | "sent" | "error";

export function DeleteAccountCard() {
  const [acknowledged, setAcknowledged] = useState(false);
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

    const ok = await requestAccountDeletion(session.access_token);
    setStatus(ok ? "sent" : "error");
  };

  return (
    <div className="rounded-2xl border border-red-200 bg-red-50/40 p-6 shadow-sm">
      <h2 className="text-base font-semibold tracking-tight text-red-700">Delete workspace</h2>
      <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-zerqo-muted">
        Permanently delete your workspace and all of its data — calls, recordings, transcripts,
        knowledge documents, and team access. This cannot be undone. We&rsquo;ll email you a link to
        confirm before anything is deleted.
      </p>

      {status === "sent" ? (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-[13px] text-emerald-800">
          Check your email — we&rsquo;ve sent a confirmation link. Deletion only happens after you
          confirm. The link expires in 24 hours.
        </div>
      ) : status === "error" ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-100 px-4 py-3 text-[13px] text-red-700">
          Something went wrong. If this keeps happening, contact support.
        </div>
      ) : (
        <label className="mt-4 flex items-start gap-2.5 text-[13px] text-zerqo-ink">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => setAcknowledged(e.target.checked)}
            className="mt-0.5 size-4 accent-red-600"
          />
          <span>I understand this permanently deletes my workspace and all of its data.</span>
        </label>
      )}

      {status !== "sent" ? (
        <button
          type="button"
          onClick={onRequest}
          disabled={!acknowledged || status === "requesting"}
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {status === "requesting" ? (
            <>
              <Loader2 className="size-4 animate-spin" /> Sending confirmation…
            </>
          ) : (
            <>
              <Trash2 className="size-4" /> Request workspace deletion
            </>
          )}
        </button>
      ) : null}
    </div>
  );
}
