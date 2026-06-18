"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, PauseCircle, PlayCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import {
  fetchTenantDetail,
  inviteTenantLogin,
  patchTenant,
  recordTenantPayment,
  type TenantDetail,
} from "@/lib/api/internal";
import { AgentEditForm } from "@/components/internal-dashboard/agent-edit-form";
import { KnowledgeTab } from "@/components/internal-dashboard/knowledge-tab";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "agents", label: "Agents" },
  { id: "calls", label: "Calls" },
  { id: "knowledge", label: "Knowledge" },
  { id: "billing", label: "Billing" },
  { id: "audit", label: "Audit" },
] as const;

type TabId = (typeof TABS)[number]["id"];

type TenantDetailViewProps = {
  tenantId: string;
};

function statusClass(status: string) {
  if (status === "active") return "bg-emerald-100 text-emerald-800";
  if (status === "paused") return "bg-amber-100 text-amber-800";
  return "bg-zinc-200 text-zinc-700";
}

export function TenantDetailView({ tenantId }: TenantDetailViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeTab = (searchParams.get("tab") as TabId) || "overview";

  const [data, setData] = useState<TenantDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [savingAccess, setSavingAccess] = useState(false);
  const [accessDraft, setAccessDraft] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);
  const [recordingPayment, setRecordingPayment] = useState(false);
  const [paymentMsg, setPaymentMsg] = useState<string | null>(null);
  const [paymentDraft, setPaymentDraft] = useState({
    amount_inr: "",
    method: "UPI",
    plan: "starter",
    period_start: "",
    period_end: "",
    reference: "",
  });
  const [providerDraft, setProviderDraft] = useState({
    stt: "",
    tts: "",
    llm: "",
  });

  const loadDetail = useCallback(
    async (auditPage = 1) => {
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
        const detail = await fetchTenantDetail(session.access_token, tenantId, auditPage);
        setData(detail);
        setProviderDraft(detail.tenant.provider_config);
        setAccessDraft(detail.tenant.paid_until ? detail.tenant.paid_until.slice(0, 10) : "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load tenant");
      } finally {
        setLoading(false);
      }
    },
    [tenantId]
  );

  useEffect(() => {
    void loadDetail(activeTab === "audit" ? Number(searchParams.get("audit_page") ?? 1) : 1);
  }, [activeTab, loadDetail, searchParams]);

  function setTab(tab: TabId) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    if (tab !== "audit") {
      params.delete("audit_page");
    }
    router.replace(`${pathname}?${params.toString()}`);
  }

  async function saveProviderConfig() {
    if (!data) return;
    setSaving(true);
    setError(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      await patchTenant(session.access_token, tenantId, {
        provider_config: providerDraft,
      });
      await loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save provider config");
    } finally {
      setSaving(false);
    }
  }

  async function saveAccessWindow() {
    setSavingAccess(true);
    setError(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      // End-of-day in local time, sent as ISO. Empty clears the window.
      const paid_until = accessDraft ? new Date(`${accessDraft}T23:59:59`).toISOString() : null;
      await patchTenant(session.access_token, tenantId, { paid_until });
      await loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update access window");
    } finally {
      setSavingAccess(false);
    }
  }

  async function sendInvite() {
    if (!inviteEmail) return;
    setInviting(true);
    setError(null);
    setInviteMsg(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      await inviteTenantLogin(session.access_token, tenantId, inviteEmail);
      setInviteMsg(`Invite sent to ${inviteEmail}`);
      setInviteEmail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send invite");
    } finally {
      setInviting(false);
    }
  }

  async function recordPaymentFn() {
    setRecordingPayment(true);
    setError(null);
    setPaymentMsg(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    try {
      await recordTenantPayment(session.access_token, tenantId, {
        amount_inr: Number(paymentDraft.amount_inr),
        method: paymentDraft.method,
        plan: paymentDraft.plan,
        period_start: paymentDraft.period_start,
        period_end: paymentDraft.period_end,
        reference: paymentDraft.reference || undefined,
      });
      setPaymentMsg("Payment recorded — access extended.");
      await loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record payment");
    } finally {
      setRecordingPayment(false);
    }
  }

  async function updateStatus(status: "active" | "paused") {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) return;

    await patchTenant(session.access_token, tenantId, { status });
    await loadDetail();
  }

  if (loading && !data) {
    return <p className="text-muted-foreground">Loading tenant…</p>;
  }

  if (!data) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {error ?? "Tenant not found"}
      </div>
    );
  }

  const { tenant } = data;
  const maxVolume = Math.max(...data.call_volume_14d.map((point) => point.count), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <Link
          href="/internal/tenants"
          aria-label="Back to tenants"
          className={buttonVariants({ variant: "outline", size: "icon-sm" })}
        >
          <ArrowLeft className="size-4" />
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{tenant.business_name}</h1>
            <span
              className={cn(
                "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                statusClass(tenant.status)
              )}
            >
              {tenant.status}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">
            {tenant.market.replaceAll("_", " ")} · {tenant.slug}
            {tenant.contact_email ? ` · ${tenant.contact_email}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          {tenant.status === "active" ? (
            <Button variant="outline" size="sm" onClick={() => void updateStatus("paused")}>
              <PauseCircle className="mr-2 size-4" />
              Pause
            </Button>
          ) : tenant.status === "paused" ? (
            <Button variant="outline" size="sm" onClick={() => void updateStatus("active")}>
              <PlayCircle className="mr-2 size-4" />
              Resume
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-zerqo-line pb-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setTab(tab.id)}
            className={cn(
              "rounded-t-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "border-b-2 border-[#f04e00] text-[#f04e00]"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {activeTab === "overview" ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-xl border border-zerqo-line bg-white p-5">
            <h2 className="font-medium">Provider config</h2>
            <div className="mt-4 grid gap-3">
              {(["stt", "tts", "llm"] as const).map((key) => (
                <div key={key} className="space-y-1">
                  <Label htmlFor={key}>{key.toUpperCase()}</Label>
                  <Input
                    id={key}
                    value={providerDraft[key]}
                    onChange={(e) =>
                      setProviderDraft((draft) => ({ ...draft, [key]: e.target.value }))
                    }
                  />
                </div>
              ))}
            </div>
            <Button
              className="mt-4 bg-[#f04e00] hover:bg-[#d94400]"
              size="sm"
              disabled={saving}
              onClick={() => void saveProviderConfig()}
            >
              {saving ? "Saving…" : "Save config"}
            </Button>
          </section>

          <section className="rounded-xl border border-zerqo-line bg-white p-5">
            <h2 className="font-medium">Access window</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Agents answer only while the paid window is active. Past the date, the tenant is
              paused automatically.
            </p>
            <p className="mt-3 text-sm">
              <span className="text-muted-foreground">Paid until: </span>
              {tenant.paid_until ? (
                <span className="font-medium">
                  {new Date(tenant.paid_until).toLocaleDateString()}
                </span>
              ) : (
                <span className="text-muted-foreground">not set (no access)</span>
              )}
            </p>
            <div className="mt-4 space-y-1">
              <Label htmlFor="paid_until">Set paid-until date</Label>
              <Input
                id="paid_until"
                type="date"
                value={accessDraft}
                onChange={(e) => setAccessDraft(e.target.value)}
              />
            </div>
            <Button
              className="mt-4 bg-[#f04e00] hover:bg-[#d94400]"
              size="sm"
              disabled={savingAccess}
              onClick={() => void saveAccessWindow()}
            >
              {savingAccess ? "Saving…" : "Update access"}
            </Button>
          </section>

          <section className="rounded-xl border border-zerqo-line bg-white p-5">
            <h2 className="font-medium">Client login</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Invite the client to the portal — they get an email to set their password.
            </p>
            <div className="mt-4 space-y-1">
              <Label htmlFor="invite_email">Email</Label>
              <Input
                id="invite_email"
                type="email"
                placeholder="owner@business.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            {inviteMsg ? <p className="mt-2 text-sm text-emerald-700">{inviteMsg}</p> : null}
            <Button
              className="mt-4 bg-[#f04e00] hover:bg-[#d94400]"
              size="sm"
              disabled={inviting || !inviteEmail}
              onClick={() => void sendInvite()}
            >
              {inviting ? "Sending…" : "Send invite"}
            </Button>
          </section>

          <section className="rounded-xl border border-zerqo-line bg-white p-5 lg:col-span-2">
            <h2 className="font-medium">Record payment</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Log an offline payment (UPI / bank transfer). This extends the access window and
              re-activates the tenant.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="pay_amount">Amount (₹)</Label>
                <Input
                  id="pay_amount"
                  type="number"
                  min="0"
                  value={paymentDraft.amount_inr}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, amount_inr: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pay_plan">Plan</Label>
                <select
                  id="pay_plan"
                  value={paymentDraft.plan}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, plan: e.target.value }))}
                  className="h-9 w-full rounded-md border border-zerqo-line bg-white px-3 text-sm"
                >
                  <option value="starter">Starter</option>
                  <option value="growth">Growth</option>
                  <option value="pro">Pro</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="pay_method">Method</Label>
                <Input
                  id="pay_method"
                  value={paymentDraft.method}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, method: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pay_start">Period start</Label>
                <Input
                  id="pay_start"
                  type="date"
                  value={paymentDraft.period_start}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, period_start: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pay_end">Period end</Label>
                <Input
                  id="pay_end"
                  type="date"
                  value={paymentDraft.period_end}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, period_end: e.target.value }))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pay_ref">Reference (UTR)</Label>
                <Input
                  id="pay_ref"
                  value={paymentDraft.reference}
                  onChange={(e) => setPaymentDraft((d) => ({ ...d, reference: e.target.value }))}
                />
              </div>
            </div>
            {paymentMsg ? <p className="mt-2 text-sm text-emerald-700">{paymentMsg}</p> : null}
            <Button
              className="mt-4 bg-[#f04e00] hover:bg-[#d94400]"
              size="sm"
              disabled={recordingPayment || !paymentDraft.amount_inr || !paymentDraft.period_end}
              onClick={() => void recordPaymentFn()}
            >
              {recordingPayment ? "Recording…" : "Record payment"}
            </Button>
          </section>

          <section className="rounded-xl border border-zerqo-line bg-white p-5">
            <h2 className="font-medium">Call volume (14 days)</h2>
            <div className="mt-4 flex h-32 items-end gap-1">
              {data.call_volume_14d.length === 0 ? (
                <p className="text-sm text-muted-foreground">No calls in the last 14 days.</p>
              ) : (
                data.call_volume_14d.map((point) => (
                  <div key={point.day} className="flex flex-1 flex-col items-center gap-1">
                    <div
                      className="w-full rounded-t bg-[#f04e00]/80"
                      style={{ height: `${(point.count / maxVolume) * 100}%`, minHeight: 4 }}
                      title={`${point.day}: ${point.count}`}
                    />
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rounded-xl border border-zerqo-line bg-white p-5 lg:col-span-2">
            <h2 className="font-medium">Latest calls</h2>
            {data.recent_calls.length === 0 ? (
              <p className="mt-3 text-sm text-muted-foreground">No calls yet.</p>
            ) : (
              <ul className="mt-3 divide-y divide-zerqo-line/70">
                {data.recent_calls.map((call) => (
                  <li key={call.id} className="flex justify-between py-2 text-sm">
                    <span>{call.from_number}</span>
                    <span className="text-muted-foreground">
                      {new Date(call.started_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : null}

      {activeTab === "agents" ? (
        <div className="space-y-4">
          {data.agents.length === 0 ? (
            <p className="rounded-xl border border-zerqo-line bg-white p-5 text-sm text-muted-foreground">
              No agents yet.
            </p>
          ) : (
            data.agents.map((agent) => (
              <AgentEditForm
                key={agent.id}
                tenantId={tenantId}
                agent={agent}
                onSaved={() => void loadDetail()}
              />
            ))
          )}
        </div>
      ) : null}

      {activeTab === "calls" ? (
        <section className="rounded-xl border border-zerqo-line bg-white p-5">
          {data.recent_calls.length === 0 ? (
            <p className="text-sm text-muted-foreground">No calls recorded for this tenant.</p>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="border-b border-zerqo-line text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-2 text-left">From</th>
                  <th className="py-2 text-left">Started</th>
                  <th className="py-2 text-left">Duration</th>
                  <th className="py-2 text-left">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_calls.map((call) => (
                  <tr key={call.id} className="border-b border-zerqo-line/70">
                    <td className="py-2">{call.from_number}</td>
                    <td className="py-2">{new Date(call.started_at).toLocaleString()}</td>
                    <td className="py-2">{call.duration_secs ?? "—"}s</td>
                    <td className="py-2">{call.outcome ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ) : null}

      {activeTab === "knowledge" ? <KnowledgeTab tenantId={tenantId} /> : null}

      {activeTab === "billing" ? (
        <section className="rounded-xl border border-dashed border-zerqo-line bg-white p-8 text-center text-sm text-muted-foreground">
          Billing details arrive in Phase 5.
        </section>
      ) : null}

      {activeTab === "audit" ? (
        <section className="rounded-xl border border-zerqo-line bg-white">
          {data.audit_log.length === 0 ? (
            <p className="p-5 text-sm text-muted-foreground">No audit events for this tenant.</p>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="border-b border-zerqo-line bg-[#faf7f3] text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 text-left">When</th>
                  <th className="px-4 py-3 text-left">Action</th>
                  <th className="px-4 py-3 text-left">Actor</th>
                </tr>
              </thead>
              <tbody>
                {data.audit_log.map((entry) => (
                  <tr key={entry.id} className="border-b border-zerqo-line/70">
                    <td className="px-4 py-3">{new Date(entry.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 font-mono text-xs">{entry.action}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {entry.actor_user_id ?? "system"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ) : null}
    </div>
  );
}
