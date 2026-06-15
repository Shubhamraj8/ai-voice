"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { fetchAuditLog, type AuditLogQuery, type AuditLogRow } from "@/lib/api/internal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const PAGE_SIZE = 50;

const SELECT_CLASS =
  "h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm " +
  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

const CSV_HEADERS = [
  "created_at",
  "actor_email",
  "actor_type",
  "action",
  "target_type",
  "target_id",
  "tenant_id",
] as const;

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

function toCsv(rows: AuditLogRow[]): string {
  const escape = (value: unknown) => {
    const s = value == null ? "" : String(value);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [CSV_HEADERS.join(",")];
  for (const row of rows) {
    lines.push(CSV_HEADERS.map((h) => escape((row as Record<string, unknown>)[h])).join(","));
  }
  return lines.join("\n");
}

function downloadCsv(rows: AuditLogRow[]) {
  const blob = new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "audit-log.csv";
  link.click();
  URL.revokeObjectURL(url);
}

export function AuditLogViewer() {
  const searchParams = useSearchParams();
  const tenantFilter = searchParams.get("tenant") ?? "";

  const [actorType, setActorType] = useState("");
  const [action, setAction] = useState("");
  const [targetType, setTargetType] = useState("");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [rows, setRows] = useState<AuditLogRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = useCallback(
    async (targetPage: number) => {
      setLoading(true);
      setError(null);
      try {
        const token = await getAccessToken();
        if (!token) {
          setError("Not signed in");
          return;
        }
        const params: AuditLogQuery = {
          page: targetPage,
          page_size: PAGE_SIZE,
          actor_type: actorType || undefined,
          action: action || undefined,
          target_type: targetType || undefined,
          tenant: tenantFilter || undefined,
          search: search || undefined,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
        };
        const result = await fetchAuditLog(token, params);
        setRows(result.items);
        setTotal(result.total);
        setPage(result.page);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load audit log");
      } finally {
        setLoading(false);
      }
    },
    [actorType, action, targetType, tenantFilter, search, dateFrom, dateTo]
  );

  // Initial load and whenever the tenant filter (from the URL) changes.
  useEffect(() => {
    void load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantFilter]);

  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
          <p className="text-sm text-muted-foreground">
            {total} event{total === 1 ? "" : "s"}
            {tenantFilter ? " (filtered to one tenant)" : ""}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={rows.length === 0}
          onClick={() => downloadCsv(rows)}
        >
          Export CSV
        </Button>
      </div>

      <section className="grid gap-3 rounded-xl border border-zerqo-line bg-white p-4 sm:grid-cols-3 lg:grid-cols-6">
        <div className="space-y-1">
          <Label htmlFor="actor_type">Actor</Label>
          <select
            id="actor_type"
            className={SELECT_CLASS + " w-full"}
            value={actorType}
            onChange={(e) => setActorType(e.target.value)}
          >
            <option value="">All</option>
            <option value="internal_user">Internal</option>
            <option value="tenant_user">Tenant</option>
            <option value="system">System</option>
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="target_type">Target</Label>
          <select
            id="target_type"
            className={SELECT_CLASS + " w-full"}
            value={targetType}
            onChange={(e) => setTargetType(e.target.value)}
          >
            <option value="">All</option>
            <option value="tenant">Tenant</option>
            <option value="agent">Agent</option>
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="action">Action contains</Label>
          <Input
            id="action"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            placeholder="agent.update"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="search">Search (email / target id)</Label>
          <Input id="search" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="date_from">From</Label>
          <Input
            id="date_from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="date_to">To</Label>
          <Input
            id="date_to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <div className="sm:col-span-3 lg:col-span-6">
          <Button
            className="bg-[#f04e00] hover:bg-[#d94400]"
            size="sm"
            disabled={loading}
            onClick={() => void load(1)}
          >
            {loading ? "Loading…" : "Apply filters"}
          </Button>
        </div>
      </section>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <section className="overflow-hidden rounded-xl border border-zerqo-line bg-white">
        {rows.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">No audit events.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="border-b border-zerqo-line bg-[#faf7f3] text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left">When</th>
                <th className="px-4 py-3 text-left">Actor</th>
                <th className="px-4 py-3 text-left">Action</th>
                <th className="px-4 py-3 text-left">Target</th>
                <th className="px-4 py-3 text-left" />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <Fragment key={row.id}>
                  <tr className="border-b border-zerqo-line/70">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">{row.actor_email ?? row.actor_type}</td>
                    <td className="px-4 py-3 font-mono text-xs">{row.action}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {row.target_type ? `${row.target_type}:${row.target_id ?? ""}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {row.payload ? (
                        <button
                          type="button"
                          className="text-xs text-[#f04e00]"
                          aria-expanded={expanded === row.id}
                          onClick={() => setExpanded(expanded === row.id ? null : row.id)}
                        >
                          {expanded === row.id ? "Hide" : "Details"}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                  {expanded === row.id && row.payload ? (
                    <tr className="border-b border-zerqo-line/70">
                      <td colSpan={5} className="bg-[#faf7f3] px-4 py-3">
                        <pre className="overflow-x-auto text-xs">
                          {JSON.stringify(row.payload, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          Page {page} of {lastPage}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={loading || page <= 1}
            onClick={() => void load(page - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={loading || page >= lastPage}
            onClick={() => void load(page + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
