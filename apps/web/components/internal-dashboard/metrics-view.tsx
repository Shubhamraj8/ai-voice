"use client";

import { useEffect, useState } from "react";
import { Building2, Clock, Phone, Timer } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { fetchPlatformMetrics, type PlatformMetrics } from "@/lib/api/internal";
import { cn } from "@/lib/utils";

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

function ms(value: number | null): string {
  return value == null ? "—" : `${value} ms`;
}

function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

function Kpi({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Phone;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card>
      <div className="flex items-center gap-2 text-zerqo-muted">
        <Icon className="size-4" />
        <span className="text-[13px] font-semibold">{label}</span>
      </div>
      <p className="mt-3 text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">{value}</p>
      {sub ? <p className="mt-1 text-[13px] text-zerqo-muted">{sub}</p> : null}
    </Card>
  );
}

export function MetricsView() {
  const [data, setData] = useState<PlatformMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (!token) {
        setError("Session expired — please refresh.");
        return;
      }
      try {
        setData(await fetchPlatformMetrics(token));
      } catch {
        setError("Couldn’t load metrics.");
      }
    })();
  }, []);

  const latencyRows: { label: string; p: PlatformMetrics["latency"]["total_ms"] }[] = data
    ? [
        { label: "STT", p: data.latency.stt_ms },
        { label: "LLM", p: data.latency.llm_ms },
        { label: "TTS first byte", p: data.latency.tts_first_byte_ms },
        { label: "Total / turn", p: data.latency.total_ms },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Internal ops</span>
        </div>
        <h1 className="text-[clamp(24px,3vw,32px)] font-semibold tracking-tight text-zerqo-ink">
          Metrics
        </h1>
        <p className="mt-2 text-[15px] text-zerqo-muted">
          Platform usage, latency, and health KPIs.
        </p>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi
          icon={Building2}
          label="Tenants"
          value={data ? String(data.tenants.total) : "—"}
          sub={data ? `${data.tenants.active} active · ${data.tenants.paused} paused` : undefined}
        />
        <Kpi
          icon={Phone}
          label="Calls (total)"
          value={data ? String(data.calls.total) : "—"}
          sub={data ? `${data.calls.last_24h} in last 24h` : undefined}
        />
        <Kpi icon={Timer} label="Minutes handled" value={data ? String(data.minutes_total) : "—"} />
        <Kpi
          icon={Clock}
          label="P95 latency / turn"
          value={data ? ms(data.latency.total_ms.p95) : "—"}
          sub={data ? `over ${data.latency.sample_size} turns` : undefined}
        />
      </div>

      <Card>
        <h2 className="mb-4 text-base font-semibold tracking-tight text-zerqo-ink">
          Per-turn latency (p50 / p95 / p99)
        </h2>
        <div className="overflow-hidden rounded-xl border border-zerqo-line">
          <div className="grid grid-cols-4 gap-3 border-b border-zerqo-line bg-zerqo-cream/40 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-zerqo-muted">
            <span>Segment</span>
            <span className="text-right">p50</span>
            <span className="text-right">p95</span>
            <span className="text-right">p99</span>
          </div>
          {latencyRows.length === 0 ? (
            <p className="px-4 py-4 text-[13px] text-zerqo-muted">No latency samples yet.</p>
          ) : (
            <div className="divide-y divide-zerqo-line">
              {latencyRows.map((row) => (
                <div
                  key={row.label}
                  className="grid grid-cols-4 gap-3 px-4 py-2.5 text-sm tabular-nums text-zerqo-ink"
                >
                  <span className="font-medium">{row.label}</span>
                  <span className="text-right text-zerqo-muted">{ms(row.p.p50)}</span>
                  <span className="text-right">{ms(row.p.p95)}</span>
                  <span className="text-right text-zerqo-muted">{ms(row.p.p99)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
