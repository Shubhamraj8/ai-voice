"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { fetchLeads, updateLeadStatus, type Lead, type LeadStatus } from "@/lib/api/internal";
import { cn } from "@/lib/utils";

const STATUSES: LeadStatus[] = ["new", "contacted", "converted", "lost"];

const STATUS_CLASS: Record<LeadStatus, string> = {
  new: "bg-blue-100 text-blue-800",
  contacted: "bg-amber-100 text-amber-800",
  converted: "bg-emerald-100 text-emerald-800",
  lost: "bg-zinc-200 text-zinc-700",
};

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function LeadsInbox() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<LeadStatus | "all">("all");

  const load = useCallback(async () => {
    setLoading(true);
    const token = await getToken();
    if (!token) {
      setError("Not signed in");
      setLoading(false);
      return;
    }
    try {
      setLeads(await fetchLeads(token, filter === "all" ? undefined : filter));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function changeStatus(lead: Lead, status: LeadStatus) {
    const token = await getToken();
    if (!token) return;
    try {
      await updateLeadStatus(token, lead.id, status);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update lead");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {(["all", ...STATUSES] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setFilter(s)}
            className={cn(
              "rounded-full px-3 py-1 text-sm font-medium capitalize transition-colors",
              filter === s
                ? "bg-[#f04e00] text-white"
                : "bg-white text-muted-foreground hover:text-foreground"
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <section className="rounded-xl border border-zerqo-line bg-white">
        {loading && leads.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">Loading leads…</p>
        ) : leads.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">No leads yet.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="border-b border-zerqo-line text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left">Business</th>
                <th className="px-4 py-3 text-left">Contact</th>
                <th className="px-4 py-3 text-left">Source</th>
                <th className="px-4 py-3 text-left">Received</th>
                <th className="px-4 py-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b border-zerqo-line/70 align-top">
                  <td className="px-4 py-3">{lead.business_name ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div>{lead.contact_name ?? "—"}</div>
                    <div className="text-muted-foreground">{lead.contact_email}</div>
                    {lead.contact_phone ? (
                      <div className="text-muted-foreground">{lead.contact_phone}</div>
                    ) : null}
                    {lead.message ? (
                      <div className="mt-1 max-w-xs text-xs text-muted-foreground">
                        {lead.message}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{lead.source ?? "—"}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(lead.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "mb-2 inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        STATUS_CLASS[lead.status]
                      )}
                    >
                      {lead.status}
                    </span>
                    <select
                      value={lead.status}
                      onChange={(e) => void changeStatus(lead, e.target.value as LeadStatus)}
                      className="block rounded-md border border-zerqo-line bg-white px-2 py-1 text-xs"
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
