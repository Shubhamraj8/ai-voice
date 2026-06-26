"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Phone } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import { fetchInternalCalls, type InternalCallsPage } from "@/lib/api/internal";
import { formatDateTime, formatDuration, maskPhone } from "@/lib/format";
import { cn } from "@/lib/utils";

const OUTCOME_LABEL: Record<string, string> = {
  booked: "Booked",
  transferred: "Transferred",
  info_only: "Info",
  abandoned: "Abandoned",
};

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function InternalCallsView() {
  const [data, setData] = useState<InternalCallsPage | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    const token = await getToken();
    if (!token) {
      setError("Session expired — please refresh.");
      setLoading(false);
      return;
    }
    try {
      setData(await fetchInternalCalls(token, { page: p }));
    } catch {
      setError("Couldn’t load calls.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page);
  }, [page, load]);

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 25;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Internal ops</span>
        </div>
        <h1 className="text-[clamp(24px,3vw,32px)] font-semibold tracking-tight text-zerqo-ink">
          Calls
        </h1>
        <p className="mt-2 text-[15px] text-zerqo-muted">
          Recent calls across all tenants, newest first.
        </p>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      ) : null}

      <div
        className={cn(
          "overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm transition-opacity",
          loading && "opacity-60"
        )}
      >
        <div className="hidden grid-cols-[1.4fr_150px_140px_80px_110px_1fr] gap-3 border-b border-zerqo-line px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-zerqo-muted lg:grid">
          <span>Tenant</span>
          <span>Started</span>
          <span>Caller</span>
          <span>Duration</span>
          <span>Outcome</span>
          <span>Intent</span>
        </div>
        {items.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Phone className="size-7 text-zerqo-muted" />
            <p className="mt-3 text-sm font-medium text-zerqo-ink">No calls yet</p>
          </div>
        ) : (
          <div className="divide-y divide-zerqo-line">
            {items.map((call) => (
              <Link
                key={call.id}
                href={`/internal/tenants/${call.tenant_id}`}
                className="grid grid-cols-2 gap-x-3 gap-y-1 px-5 py-3 text-sm transition-colors hover:bg-zerqo-cream/60 lg:grid-cols-[1.4fr_150px_140px_80px_110px_1fr] lg:items-center"
              >
                <span className="order-1 truncate font-medium text-zerqo-ink">
                  {call.tenant_name}
                </span>
                <span className="order-2 text-[13px] text-zerqo-muted lg:text-zerqo-ink">
                  {formatDateTime(call.started_at)}
                </span>
                <span className="order-4 tabular-nums text-zerqo-ink lg:order-3">
                  {maskPhone(call.from_number)}
                </span>
                <span className="order-5 tabular-nums text-zerqo-muted lg:order-4 lg:text-zerqo-ink">
                  {formatDuration(call.duration_secs)}
                </span>
                <span className="order-3 lg:order-5">
                  {call.outcome ? (
                    <span className="rounded-full bg-zerqo-orange-soft px-2 py-0.5 text-[11px] font-medium text-zerqo-orange">
                      {OUTCOME_LABEL[call.outcome] ?? call.outcome}
                    </span>
                  ) : (
                    <span className="text-zerqo-muted">—</span>
                  )}
                </span>
                <span className="order-6 truncate text-[13px] text-zerqo-muted">
                  {call.intent ?? "—"}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {total > 0 ? (
        <div className="flex items-center justify-between text-[13px] text-zerqo-muted">
          <span>
            {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="inline-flex items-center gap-1 rounded-lg border border-zerqo-line bg-white px-3 py-1.5 font-medium text-zerqo-ink transition-colors hover:bg-zerqo-cream/60 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="size-4" /> Prev
            </button>
            <span className="tabular-nums">
              {page} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="inline-flex items-center gap-1 rounded-lg border border-zerqo-line bg-white px-3 py-1.5 font-medium text-zerqo-ink transition-colors hover:bg-zerqo-cream/60 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next <ChevronRight className="size-4" />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
