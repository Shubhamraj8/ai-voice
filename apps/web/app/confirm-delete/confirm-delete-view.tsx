"use client";

import { useState } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

import { confirmAccountDeletion } from "@/lib/api/portal";

type Status = "idle" | "working" | "done" | "error";

export function ConfirmDeleteView({ token }: { token: string | null }) {
  const [status, setStatus] = useState<Status>("idle");

  if (!token) {
    return (
      <Shell>
        <h1 className="text-xl font-semibold text-zerqo-ink">Invalid link</h1>
        <p className="mt-2 text-sm text-zerqo-muted">
          This deletion link is missing or malformed. Please use the link from your email.
        </p>
      </Shell>
    );
  }

  if (status === "done") {
    return (
      <Shell>
        <h1 className="text-xl font-semibold text-zerqo-ink">Deletion started</h1>
        <p className="mt-2 text-sm text-zerqo-muted">
          Your workspace and all its data are being permanently deleted. We&rsquo;ll email you once
          it&rsquo;s complete.
        </p>
      </Shell>
    );
  }

  const onConfirm = async () => {
    setStatus("working");
    const ok = await confirmAccountDeletion(token);
    setStatus(ok ? "done" : "error");
  };

  return (
    <Shell>
      <div className="flex items-center gap-2 text-red-600">
        <AlertTriangle className="size-5" />
        <h1 className="text-xl font-semibold text-zerqo-ink">Confirm permanent deletion</h1>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-zerqo-muted">
        This will permanently delete your ZERQO workspace and all of its data — calls, recordings,
        transcripts, knowledge documents, and team access. This cannot be undone.
      </p>

      {status === "error" ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          This link is invalid, already used, or expired. Please request deletion again from your
          settings.
        </div>
      ) : null}

      <button
        type="button"
        onClick={onConfirm}
        disabled={status === "working"}
        className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {status === "working" ? (
          <>
            <Loader2 className="size-4 animate-spin" /> Deleting…
          </>
        ) : (
          "Permanently delete everything"
        )}
      </button>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zerqo-cream/40 px-4">
      <div className="w-full max-w-md rounded-2xl border border-zerqo-line bg-white p-8 shadow-sm">
        {children}
      </div>
    </main>
  );
}
