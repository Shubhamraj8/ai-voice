import { AlertTriangle, CalendarClock, IndianRupee, Timer } from "lucide-react";

import type { BillingEvent, BillingSummary } from "@/lib/api/portal";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

type BillingViewProps = {
  summary: BillingSummary | null;
  events: BillingEvent[];
  businessName: string;
};

function formatInr(value: number | null | undefined): string {
  if (value == null) return "—";
  return `₹${value.toLocaleString("en-IN")}`;
}

function str(value: unknown): string | null {
  return typeof value === "string" || typeof value === "number" ? String(value) : null;
}

function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

function ExpiryBanner({ summary, renewHref }: { summary: BillingSummary; renewHref: string }) {
  const { expiry_state, paid_until, days_remaining } = summary.access;
  if (expiry_state !== "expiring_soon" && expiry_state !== "expired") return null;

  const expired = expiry_state === "expired";
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 rounded-2xl border p-4",
        expired ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50"
      )}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle
          className={cn("mt-0.5 size-5", expired ? "text-red-600" : "text-amber-600")}
        />
        <div>
          <p className="text-sm font-semibold text-zerqo-ink">
            {expired ? "Your access has expired" : "Your access is ending soon"}
          </p>
          <p className="mt-0.5 text-[13px] text-zerqo-muted">
            {expired
              ? `Access ended on ${formatDate(paid_until)} and your agents are paused.`
              : `Access ends ${formatDate(paid_until)}${
                  days_remaining != null
                    ? ` (${days_remaining} day${days_remaining === 1 ? "" : "s"} left)`
                    : ""
                }.`}{" "}
            Contact us to renew.
          </p>
        </div>
      </div>
      <a
        href={renewHref}
        className="shrink-0 rounded-xl bg-zerqo-orange px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-zerqo-orange/90"
      >
        Contact us to renew
      </a>
    </div>
  );
}

function PlanCard({ summary, renewHref }: { summary: BillingSummary; renewHref: string }) {
  const { plan } = summary;
  return (
    <Card>
      <div className="mb-4 flex items-center gap-2 text-zerqo-muted">
        <CalendarClock className="size-4" />
        <span className="text-[13px] font-semibold">Plan</span>
      </div>
      <p className="text-2xl font-semibold capitalize tracking-tight text-zerqo-ink">
        {plan.name ?? plan.key}
      </p>
      <p className="mt-1 text-[13px] text-zerqo-muted">
        {plan.included_minutes > 0
          ? `${plan.included_minutes} minutes included / month`
          : "Custom plan"}
      </p>
      <div className="mt-4 rounded-xl border border-zerqo-line bg-zerqo-cream/60 p-3">
        <p className="font-mono text-[11px] uppercase tracking-wider text-zerqo-muted">
          Access valid until
        </p>
        <p className="mt-1 text-sm font-medium text-zerqo-ink">
          {plan.paid_until ? formatDate(plan.paid_until) : "No active access window"}
        </p>
      </div>
      <a
        href={renewHref}
        className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-zerqo-orange px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-zerqo-orange/90"
      >
        Contact us to renew
      </a>
    </Card>
  );
}

function UsageCard({ summary }: { summary: BillingSummary }) {
  const { usage } = summary;
  const pct =
    usage.included_minutes > 0
      ? Math.min(100, Math.round((usage.minutes_used / usage.included_minutes) * 100))
      : null;

  return (
    <Card>
      <div className="mb-4 flex items-center gap-2 text-zerqo-muted">
        <Timer className="size-4" />
        <span className="text-[13px] font-semibold">Usage this cycle</span>
      </div>
      <p className="text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">
        {usage.minutes_used}
        {usage.included_minutes > 0 ? (
          <span className="text-base font-medium text-zerqo-muted">
            {" "}
            / {usage.included_minutes} min
          </span>
        ) : (
          <span className="text-base font-medium text-zerqo-muted"> min</span>
        )}
      </p>
      {pct !== null ? (
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-zerqo-line">
          <div
            className={cn(
              "h-full rounded-full",
              usage.overage_minutes > 0 ? "bg-red-500" : "bg-zerqo-orange"
            )}
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
      <dl className="mt-5 grid grid-cols-2 gap-4 text-[13px]">
        <div>
          <dt className="text-zerqo-muted">Projected (end of cycle)</dt>
          <dd className="mt-0.5 font-semibold tabular-nums text-zerqo-ink">
            {usage.projected_minutes} min
          </dd>
        </div>
        <div>
          <dt className="text-zerqo-muted">Overage so far</dt>
          <dd
            className={cn(
              "mt-0.5 font-semibold tabular-nums",
              usage.overage_minutes > 0 ? "text-red-600" : "text-zerqo-ink"
            )}
          >
            {usage.overage_minutes} min
          </dd>
        </div>
      </dl>
      <p className="mt-4 text-[11px] text-zerqo-muted">
        Cycle {formatDate(usage.cycle_start)} – {formatDate(usage.cycle_end)}
      </p>
    </Card>
  );
}

function describeEvent(event: BillingEvent): {
  title: string;
  subtitle: string | null;
  amount: string | null;
  when: string;
} {
  const meta = event.metadata ?? {};
  switch (event.event_type) {
    case "payment_recorded": {
      const parts = [str(meta.method), str(meta.plan)].filter(Boolean);
      return {
        title: "Payment received",
        subtitle: parts.length ? parts.join(" · ") : null,
        amount: formatInr(event.amount_inr),
        when: formatDate(event.created_at),
      };
    }
    case "usage_reported": {
      const overage = str(meta.overage_minutes);
      const subtitle =
        overage && Number(overage) > 0
          ? `${str(meta.day_minutes) ?? event.units} min · ${overage} min overage`
          : `${str(meta.day_minutes) ?? event.units} min`;
      return {
        title: "Daily usage",
        subtitle,
        amount: null,
        when: str(meta.date) ? formatDate(String(meta.date)) : formatDate(event.created_at),
      };
    }
    case "access_extended":
      return {
        title: "Access extended",
        subtitle: null,
        amount: null,
        when: formatDate(event.created_at),
      };
    case "plan_changed":
      return {
        title: "Plan changed",
        subtitle: null,
        amount: null,
        when: formatDate(event.created_at),
      };
    default:
      return {
        title: event.event_type,
        subtitle: null,
        amount: null,
        when: formatDate(event.created_at),
      };
  }
}

function LedgerCard({ events }: { events: BillingEvent[] }) {
  return (
    <Card>
      <h2 className="mb-2 text-base font-semibold tracking-tight text-zerqo-ink">
        Payment history
      </h2>
      {events.length === 0 ? (
        <p className="py-6 text-center text-[13px] text-zerqo-muted">No billing activity yet.</p>
      ) : (
        <div className="-mx-2 divide-y divide-zerqo-line">
          {events.map((event) => {
            const { title, subtitle, amount, when } = describeEvent(event);
            const isPayment = event.event_type === "payment_recorded";
            return (
              <div key={event.id} className="flex items-center justify-between gap-4 px-2 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center rounded-full",
                      isPayment
                        ? "bg-zerqo-orange-soft text-zerqo-orange"
                        : "bg-zerqo-cream text-zerqo-muted"
                    )}
                  >
                    {isPayment ? <IndianRupee className="size-4" /> : <Timer className="size-4" />}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-zerqo-ink">{title}</p>
                    {subtitle ? (
                      <p className="truncate text-[12px] text-zerqo-muted">{subtitle}</p>
                    ) : null}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  {amount ? (
                    <p className="text-sm font-semibold tabular-nums text-zerqo-ink">{amount}</p>
                  ) : null}
                  <p className="text-[12px] text-zerqo-muted">{when}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

export function BillingView({ summary, events, businessName }: BillingViewProps) {
  const renewHref = `mailto:sales@zerqo.com?subject=${encodeURIComponent(
    `Renew plan — ${businessName}`
  )}`;

  if (!summary) {
    return (
      <Card>
        <p className="text-sm font-medium text-zerqo-ink">We couldn&rsquo;t load your billing</p>
        <p className="mt-1 text-[13px] text-zerqo-muted">Please refresh and try again.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
        </div>
        <h1 className="text-[clamp(24px,3vw,32px)] font-semibold tracking-tight text-zerqo-ink">
          Billing
        </h1>
      </div>

      <ExpiryBanner summary={summary} renewHref={renewHref} />

      <div className="grid gap-4 lg:grid-cols-2">
        <PlanCard summary={summary} renewHref={renewHref} />
        <UsageCard summary={summary} />
      </div>

      <LedgerCard events={events} />
    </div>
  );
}
