import Link from "next/link";
import { AlertTriangle, ArrowLeft, Wrench } from "lucide-react";

import type { CallDetail, ToolDispatch, TranscriptMessage } from "@/lib/api/portal";
import { formatDateTime, formatDuration, maskPhone } from "@/lib/format";
import { cn } from "@/lib/utils";
import { DownloadTranscriptButton } from "./download-transcript-button";

const OUTCOME_LABEL: Record<string, string> = {
  booked: "Booked",
  transferred: "Transferred",
  info_only: "Info",
  abandoned: "Abandoned",
};

const URGENCY_STYLE: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-zerqo-orange-soft text-zerqo-orange",
};

function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-[11px] uppercase tracking-wider text-zerqo-muted">{label}</p>
      <p className="mt-0.5 text-sm font-medium text-zerqo-ink">{value}</p>
    </div>
  );
}

function TranscriptRow({ message }: { message: TranscriptMessage }) {
  const isAgent = message.role === "assistant";
  return (
    <div className={cn("flex flex-col", isAgent ? "items-start" : "items-end")}>
      <div className="mb-1 flex items-center gap-2 text-[11px] text-zerqo-muted">
        <span className="font-semibold uppercase tracking-wider">
          {isAgent ? "Agent" : "Caller"}
        </span>
        <span>
          {new Date(message.created_at).toLocaleTimeString("en-IN", {
            hour: "numeric",
            minute: "2-digit",
            second: "2-digit",
          })}
        </span>
      </div>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isAgent ? "bg-zerqo-cream/70 text-zerqo-ink" : "bg-zerqo-orange text-white"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

function ToolRow({ tool }: { tool: ToolDispatch }) {
  const entries = Object.entries(tool.tool_args ?? {});
  return (
    <div className="rounded-xl border border-zerqo-line p-4">
      <div className="flex items-center gap-2">
        <Wrench className="size-4 text-zerqo-orange" />
        <span className="font-mono text-[13px] font-semibold text-zerqo-ink">{tool.tool_name}</span>
        <span className="ml-auto text-[11px] text-zerqo-muted">
          {formatDateTime(tool.created_at)}
        </span>
      </div>
      {entries.length > 0 ? (
        <dl className="mt-3 grid gap-1.5 text-[13px]">
          {entries.map(([key, value]) => (
            <div key={key} className="flex gap-2">
              <dt className="shrink-0 font-medium text-zerqo-muted">{key}</dt>
              <dd className="min-w-0 break-words text-zerqo-ink">{String(value)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

export function CallDetailView({ call }: { call: CallDetail }) {
  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/portal/calls"
          className="mb-4 inline-flex items-center gap-1.5 text-[13px] font-medium text-zerqo-muted transition-colors hover:text-zerqo-ink"
        >
          <ArrowLeft className="size-4" /> Back to calls
        </Link>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2.5">
              <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
              <span className="font-mono text-xs font-medium text-zerqo-muted">
                Call {call.id.slice(0, 8)}
              </span>
            </div>
            <h1 className="text-[clamp(22px,3vw,30px)] font-semibold tracking-tight text-zerqo-ink">
              {maskPhone(call.from_number)}
            </h1>
          </div>
          <DownloadTranscriptButton transcript={call.transcript} callId={call.id} />
        </div>
      </div>

      {/* Header meta + summary */}
      <Card>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <MetaItem label="Started" value={formatDateTime(call.started_at)} />
          <MetaItem label="Ended" value={call.ended_at ? formatDateTime(call.ended_at) : "—"} />
          <MetaItem label="Duration" value={formatDuration(call.duration_secs)} />
          <MetaItem label="Agent" value={call.agent_name ?? "—"} />
        </div>

        {(call.summary || call.intent || call.outcome) && (
          <div className="mt-5 border-t border-zerqo-line pt-5">
            <div className="flex flex-wrap items-center gap-2">
              {call.outcome ? (
                <span className="rounded-full bg-zerqo-orange-soft px-2.5 py-0.5 text-[12px] font-medium text-zerqo-orange">
                  {OUTCOME_LABEL[call.outcome] ?? call.outcome}
                </span>
              ) : null}
              {call.intent ? (
                <span className="rounded-full border border-zerqo-line px-2.5 py-0.5 text-[12px] font-medium text-zerqo-muted">
                  {call.intent}
                </span>
              ) : null}
            </div>
            {call.summary ? (
              <p className="mt-3 text-sm leading-relaxed text-zerqo-ink">{call.summary}</p>
            ) : null}
          </div>
        )}
      </Card>

      {/* Recording */}
      {call.recording_signed_url ? (
        <Card>
          <h2 className="mb-3 text-base font-semibold tracking-tight text-zerqo-ink">Recording</h2>
          <audio controls preload="none" src={call.recording_signed_url} className="w-full">
            Your browser does not support audio playback.
          </audio>
        </Card>
      ) : call.recording_expired ? (
        <Card>
          <h2 className="mb-2 text-base font-semibold tracking-tight text-zerqo-ink">Recording</h2>
          <p className="text-sm text-zerqo-muted">
            Recording expired — call audio is automatically removed after 30 days. The transcript is
            kept below.
          </p>
        </Card>
      ) : null}

      {/* Escalation */}
      {call.escalation ? (
        <Card className="border-red-200 bg-red-50/50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 text-red-600" />
            <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">Escalated</h2>
            <span
              className={cn(
                "ml-1 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize",
                URGENCY_STYLE[call.escalation.urgency] ?? "bg-zerqo-line text-zerqo-muted"
              )}
            >
              {call.escalation.urgency}
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-zerqo-ink">{call.escalation.summary}</p>
        </Card>
      ) : null}

      {/* Transcript */}
      <Card>
        <h2 className="mb-4 text-base font-semibold tracking-tight text-zerqo-ink">Transcript</h2>
        {call.transcript.length === 0 ? (
          <p className="text-sm text-zerqo-muted">No transcript was recorded for this call.</p>
        ) : (
          <div className="space-y-4">
            {call.transcript.map((message, i) => (
              <TranscriptRow key={i} message={message} />
            ))}
          </div>
        )}
      </Card>

      {/* Tools */}
      {call.tools.length > 0 ? (
        <Card>
          <h2 className="mb-4 text-base font-semibold tracking-tight text-zerqo-ink">
            Tools called
          </h2>
          <div className="space-y-3">
            {call.tools.map((tool, i) => (
              <ToolRow key={i} tool={tool} />
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
