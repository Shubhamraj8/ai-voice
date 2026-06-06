"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowUpDown, Plus, Search } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { fetchTenantList, type TenantListItem } from "@/lib/api/internal";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const MARKETS = [
  { value: "", label: "All markets" },
  { value: "india_english", label: "India English" },
  { value: "india_hindi", label: "India Hindi" },
  { value: "us_english", label: "US English" },
  { value: "us_hipaa", label: "US HIPAA" },
  { value: "global_english", label: "Global English" },
] as const;

const STATUSES = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "paused", label: "Paused" },
  { value: "churned", label: "Churned" },
] as const;

const SORT_OPTIONS = [
  { value: "-created_at", label: "Newest" },
  { value: "created_at", label: "Oldest" },
  { value: "-calls_7d", label: "Most calls (7d)" },
  { value: "-mrr", label: "Highest MRR" },
] as const;

function statusClass(status: TenantListItem["status"]) {
  if (status === "active") return "bg-emerald-100 text-emerald-800";
  if (status === "paused") return "bg-amber-100 text-amber-800";
  return "bg-zinc-200 text-zinc-700";
}

function formatMarket(market: string) {
  return market.replaceAll("_", " ");
}

export function TenantsTable() {
  const [items, setItems] = useState<TenantListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [market, setMarket] = useState("");
  const [hasActiveCalls, setHasActiveCalls] = useState(false);
  const [sort, setSort] = useState("-created_at");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const loadTenants = useCallback(async () => {
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      setError("Not signed in");
      setLoading(false);
      return;
    }

    try {
      const data = await fetchTenantList(session.access_token, {
        page,
        page_size: 25,
        status: status || undefined,
        market: market || undefined,
        search: search || undefined,
        has_active_calls: hasActiveCalls,
        sort,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tenants");
    } finally {
      setLoading(false);
    }
  }, [hasActiveCalls, market, page, search, sort, status]);

  useEffect(() => {
    void loadTenants();
  }, [loadTenants]);

  const pageCount = useMemo(() => Math.max(1, Math.ceil(total / 25)), [total]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tenants</h1>
          <p className="text-sm text-muted-foreground">Manage accounts, plans, and provisioning.</p>
        </div>
        <Link
          href="/internal/tenants/new"
          className={cn(buttonVariants({ variant: "default" }), "bg-[#f04e00] hover:bg-[#d94400]")}
        >
          <Plus className="mr-2 size-4" />
          New tenant
        </Link>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search name, email, or phone…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((option) => (
            <button
              key={option.value || "all-status"}
              type="button"
              onClick={() => {
                setStatus(option.value);
                setPage(1);
              }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                status === option.value
                  ? "border-[#f04e00] bg-orange-50 text-[#f04e00]"
                  : "border-zerqo-line bg-white text-muted-foreground hover:text-foreground"
              )}
            >
              {option.label}
            </button>
          ))}
          {MARKETS.slice(1).map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                setMarket(market === option.value ? "" : option.value);
                setPage(1);
              }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                market === option.value
                  ? "border-[#f04e00] bg-orange-50 text-[#f04e00]"
                  : "border-zerqo-line bg-white text-muted-foreground hover:text-foreground"
              )}
            >
              {option.label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => {
              setHasActiveCalls((value) => !value);
              setPage(1);
            }}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              hasActiveCalls
                ? "border-[#f04e00] bg-orange-50 text-[#f04e00]"
                : "border-zerqo-line bg-white text-muted-foreground hover:text-foreground"
            )}
          >
            Active calls
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {total} tenant{total === 1 ? "" : "s"}
        </span>
        <label className="flex items-center gap-2">
          <ArrowUpDown className="size-4" />
          <select
            className="rounded-md border border-zerqo-line bg-white px-2 py-1 text-sm"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-zerqo-line bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-zerqo-line bg-[#faf7f3] text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Market</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Agents</th>
              <th className="px-4 py-3 font-medium">Calls (7d)</th>
              <th className="px-4 py-3 font-medium">MRR</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                  Loading tenants…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center">
                  <p className="font-medium">No tenants yet — create one</p>
                  <Link
                    href="/internal/tenants/new"
                    className={cn(
                      buttonVariants({ variant: "default" }),
                      "mt-4 inline-flex bg-[#f04e00] hover:bg-[#d94400]"
                    )}
                  >
                    Create tenant
                  </Link>
                </td>
              </tr>
            ) : (
              items.map((tenant) => (
                <tr
                  key={tenant.id}
                  className="border-b border-zerqo-line/70 transition-colors hover:bg-orange-50/40"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/internal/tenants/${tenant.id}`}
                      className="font-medium text-foreground hover:text-[#f04e00]"
                    >
                      {tenant.business_name}
                    </Link>
                    <p className="text-xs text-muted-foreground">{tenant.slug}</p>
                  </td>
                  <td className="px-4 py-3 capitalize">{formatMarket(tenant.market)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        statusClass(tenant.status)
                      )}
                    >
                      {tenant.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{tenant.agent_count}</td>
                  <td className="px-4 py-3">{tenant.calls_last_7d}</td>
                  <td className="px-4 py-3">${tenant.mrr_usd.toFixed(0)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pageCount > 1 ? (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1 || loading}
            onClick={() => setPage((value) => value - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount || loading}
            onClick={() => setPage((value) => value + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}
