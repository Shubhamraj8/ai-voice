"use client";

import { Download } from "lucide-react";
import type { TranscriptMessage } from "@/lib/api/portal";

function roleLabel(role: string): string {
  if (role === "assistant") return "Agent";
  if (role === "user") return "Caller";
  return role;
}

export function DownloadTranscriptButton({
  transcript,
  callId,
}: {
  transcript: TranscriptMessage[];
  callId: string;
}) {
  const onDownload = () => {
    const lines = transcript.map((m) => {
      const time = new Date(m.created_at).toLocaleTimeString("en-IN", {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      });
      return `[${time}] ${roleLabel(m.role)}: ${m.content}`;
    });
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `transcript-${callId.slice(0, 8)}.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      type="button"
      onClick={onDownload}
      disabled={transcript.length === 0}
      className="inline-flex items-center gap-2 rounded-xl border border-zerqo-line bg-white px-4 py-2 text-sm font-medium text-zerqo-ink shadow-sm transition-colors hover:bg-zerqo-cream/60 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <Download className="size-4" /> Download transcript
    </button>
  );
}
