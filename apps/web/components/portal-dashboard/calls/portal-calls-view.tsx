"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Download, Phone, Search, X } from "lucide-react";

import type { CallListPage, CallsQuery, RecentCall } from "@/lib/api/portal";
import { formatDateTime, formatDuration, maskPhone } from "@/lib/format";
import { cn } from "@/lib/utils";

const OUTCOMES: { value: string; label: string }[] = [
  { value: "booked", label: "Booked" },
  { value: "transferred", label: "Transferred" },
  { value: "info_only", label: "Info" },
  { value: "abandoned", label: "Abandoned" },
];
const OUTCOME_LABEL = Object.fromEntries(OUTCOMES.map((o) => [o.value, o.label]));

const SUMMARY_PREVIEW_CHARS = 100;

type PortalCallsViewProps = {
  data: CallListPage | null;
  query: CallsQuery;
};

function csvCell(value: string | number | null | undefined): string {
  const text = value == null ? "" : String(value);
  return `"${text.replace(/"/g, '""')}"`;
}

function exportCsv(items: RecentCall[], page: number) {
  const header = ["Started at", "Caller", "Duration (s)", "Outcome", "Intent", "Summary"];
  const lines = [header.map(csvCell).join(",")];
  for (const c of items) {
    lines.push(
      [
        c.started_at,
        c.from_number,
        c.duration_secs ?? "",
        c.outcome ?? "",
        c.intent ?? "",
        c.summary ?? "",
      ]
        .map(csvCell)
        .join(",")
    );
  }
  const blob = new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `calls-page-${page}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-[13px] font-medium transition-colors",
        active
          ? "border-zerqo-orange bg-zerqo-orange text-white"
          : "border-zerqo-line bg-white text-zerqo-muted hover:border-zerqo-orange/50 hover:text-zerqo-ink"
      )}
    >
      {children}
    </button>
  );
}

export function PortalCallsView({ data, query }: PortalCallsViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();
  const [searchInput, setSearchInput] = useState(query.search ?? "");

  // Keep the input in sync when the URL changes externally (back/forward, clear).
  useEffect(() => {
    setSearchInput(query.search ?? "");
  }, [query.search]);

  const pushQuery = useCallback(
    (next: CallsQuery) => {
      const params = new URLSearchParams();
      if (next.page && next.page > 1) params.set("page", String(next.page));
      if (next.outcome) params.set("outcome", next.outcome);
      if (next.intent) params.set("intent", next.intent);
      if (next.search) params.set("q", next.search);
      if (next.date_from) params.set("from", next.date_from);
      if (next.date_to) params.set("to", next.date_to);
      const qs = params.toString();
      startTransition(() => router.push(qs ? `${pathname}?${qs}` : pathname));
    },
    [pathname, router]
  );

  // Reset to page 1 whenever a filter changes; pagination calls pushQuery directly.
  const setFilter = useCallback(
    (patch: Partial<CallsQuery>) => {
      pushQuery({ ...query, ...patch, page: 1 });
    },
    [pushQuery, query]
  );

  // Debounced search → URL.
  useEffect(() => {
    if ((query.search ?? "") === searchInput) return;
    const handle = setTimeout(() => setFilter({ search: searchInput || undefined }), 400);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 25;
  const page = data?.page ?? query.page ?? 1;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasFilters = Boolean(
    query.outcome || query.intent || query.search || query.date_from || query.date_to
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-3 flex items-center gap-2.5">
            <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
            <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
          </div>
          <h1 className="text-[clamp(24px,3vw,32px)] font-semibold tracking-tight text-zerqo-ink">
            Calls
          </h1>
        </div>
        <button
          type="button"
          onClick={() => exportCsv(items, page)}
          disabled={items.length === 0}
          className="inline-flex items-center gap-2 rounded-xl border border-zerqo-line bg-white px-4 py-2 text-sm font-medium text-zerqo-ink shadow-sm transition-colors hover:bg-zerqo-cream/60 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Download className="size-4" /> Export CSV
        </button>
      </div>

      {/* Toolbar: search + filter chips + date range */}
      <div className="space-y-3 rounded-2xl border border-zerqo-line bg-white p-4 shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-zerqo-muted" />
          <input
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by caller number or summary…"
            className="w-full rounded-xl border border-zerqo-line bg-white py-2 pl-9 pr-3 text-sm text-zerqo-ink outline-none placeholder:text-zerqo-muted focus:border-zerqo-orange"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {OUTCOMES.map((o) => (
            <Chip
              key={o.value}
              active={query.outcome === o.value}
              onClick={() =>
                setFilter({ outcome: query.outcome === o.value ? undefined : o.value })
              }
            >
              {o.label}
            </Chip>
          ))}
          {(data?.available_intents ?? []).map((intent) => (
            <Chip
              key={intent}
              active={query.intent === intent}
              onClick={() => setFilter({ intent: query.intent === intent ? undefined : intent })}
            >
              {intent}
            </Chip>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[13px] text-zerqo-muted">
          <label className="flex items-center gap-2">
            From
            <input
              type="date"
              value={query.date_from ?? ""}
              onChange={(e) => setFilter({ date_from: e.target.value || undefined })}
              className="rounded-lg border border-zerqo-line bg-white px-2 py-1 text-zerqo-ink outline-none focus:border-zerqo-orange"
            />
          </label>
          <label className="flex items-center gap-2">
            To
            <input
              type="date"
              value={query.date_to ?? ""}
              onChange={(e) => setFilter({ date_to: e.target.value || undefined })}
              className="rounded-lg border border-zerqo-line bg-white px-2 py-1 text-zerqo-ink outline-none focus:border-zerqo-orange"
            />
          </label>
          {hasFilters ? (
            <button
              type="button"
              onClick={() => pushQuery({})}
              className="inline-flex items-center gap-1 font-medium text-zerqo-orange hover:underline"
            >
              <X className="size-3.5" /> Clear filters
            </button>
          ) : null}
        </div>
      </div>

      {/* Results */}
      {data === null ? (
        <div className="rounded-2xl border border-zerqo-line bg-white p-8 text-center shadow-sm">
          <p className="text-sm font-medium text-zerqo-ink">We couldn&rsquo;t load your calls</p>
          <p className="mt-1 text-[13px] text-zerqo-muted">Please refresh and try again.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-zerqo-line bg-white py-16 text-center shadow-sm">
          <Phone className="size-7 text-zerqo-muted" />
          <p className="mt-3 text-sm font-medium text-zerqo-ink">
            {hasFilters ? "No calls match your filters" : "No calls yet"}
          </p>
          <p className="mt-1 max-w-xs text-[13px] text-zerqo-muted">
            {hasFilters
              ? "Try adjusting or clearing your filters."
              : "Calls will appear here once your agent starts answering."}
          </p>
        </div>
      ) : (
        <div
          className={cn(
            "overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm transition-opacity",
            isPending && "opacity-60"
          )}
        >
          <div className="hidden grid-cols-[150px_140px_80px_110px_130px_1fr] gap-3 border-b border-zerqo-line px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-zerqo-muted sm:grid">
            <span>Started</span>
            <span>Caller</span>
            <span>Duration</span>
            <span>Outcome</span>
            <span>Intent</span>
            <span>Summary</span>
          </div>
          <div className="divide-y divide-zerqo-line">
            {items.map((call) => (
              <Link
                key={call.id}
                href={`/portal/calls/${call.id}`}
                className="grid grid-cols-2 gap-x-3 gap-y-1 px-5 py-3 text-sm transition-colors hover:bg-zerqo-cream/60 sm:grid-cols-[150px_140px_80px_110px_130px_1fr] sm:items-center"
              >
                <span className="order-1 text-[13px] text-zerqo-muted sm:text-zerqo-ink">
                  {formatDateTime(call.started_at)}
                </span>
                <span className="order-2 font-medium tabular-nums text-zerqo-ink">
                  {maskPhone(call.from_number)}
                </span>
                <span className="order-4 tabular-nums text-zerqo-muted sm:order-3 sm:text-zerqo-ink">
                  {formatDuration(call.duration_secs)}
                </span>
                <span className="order-3 sm:order-4">
                  {call.outcome ? (
                    <span className="rounded-full bg-zerqo-orange-soft px-2 py-0.5 text-[11px] font-medium text-zerqo-orange">
                      {OUTCOME_LABEL[call.outcome] ?? call.outcome}
                    </span>
                  ) : (
                    <span className="text-zerqo-muted">—</span>
                  )}
                </span>
                <span className="order-5 truncate text-[13px] text-zerqo-muted">
                  {call.intent ?? "—"}
                </span>
                <span className="order-6 col-span-2 truncate text-[13px] text-zerqo-muted sm:col-span-1">
                  {call.summary
                    ? call.summary.length > SUMMARY_PREVIEW_CHARS
                      ? `${call.summary.slice(0, SUMMARY_PREVIEW_CHARS)}…`
                      : call.summary
                    : "—"}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      {items.length > 0 ? (
        <div className="flex items-center justify-between text-[13px] text-zerqo-muted">
          <span>
            {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => pushQuery({ ...query, page: page - 1 })}
              disabled={page <= 1 || isPending}
              className="inline-flex items-center gap-1 rounded-lg border border-zerqo-line bg-white px-3 py-1.5 font-medium text-zerqo-ink transition-colors hover:bg-zerqo-cream/60 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="size-4" /> Prev
            </button>
            <span className="tabular-nums">
              {page} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => pushQuery({ ...query, page: page + 1 })}
              disabled={page >= totalPages || isPending}
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
