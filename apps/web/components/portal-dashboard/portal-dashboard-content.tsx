import Link from "next/link";
import { AlertTriangle, ArrowUpRight, BookOpen, CalendarClock, Phone, Timer } from "lucide-react";

import type { DashboardSummary, RecentCall } from "@/lib/api/portal";
import { formatDate, formatDateTime, formatDuration, maskPhone } from "@/lib/format";
import { cn } from "@/lib/utils";
import { CallsChart } from "./calls-chart";
import { OutboundCallCard } from "./outbound-call-card";

type PortalDashboardContentProps = {
  summary: DashboardSummary | null;
  displayName: string;
  businessName: string;
};

const OUTCOME_LABEL: Record<string, string> = {
  booked: "Booked",
  transferred: "Transferred",
  info_only: "Info",
  abandoned: "Abandoned",
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-5 flex items-center gap-2.5">
      <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
      <span className="font-mono text-xs font-medium text-zerqo-muted">{children}</span>
    </div>
  );
}

function Card({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={cn("rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}

function StatTiles({ stats }: { stats: DashboardSummary["stats"] }) {
  const pct =
    stats.minutes_included > 0
      ? Math.min(100, Math.round((stats.minutes_used / stats.minutes_included) * 100))
      : null;

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <Card>
        <div className="flex items-center gap-2 text-zerqo-muted">
          <Phone className="size-4" />
          <span className="text-[13px] font-semibold">Calls this month</span>
        </div>
        <p className="mt-3 text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">
          {stats.calls_this_month}
        </p>
      </Card>

      <Card>
        <div className="flex items-center gap-2 text-zerqo-muted">
          <Timer className="size-4" />
          <span className="text-[13px] font-semibold">Minutes used</span>
        </div>
        <p className="mt-3 text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">
          {stats.minutes_used}
          {stats.minutes_included > 0 ? (
            <span className="text-base font-medium text-zerqo-muted">
              {" "}
              / {stats.minutes_included}
            </span>
          ) : null}
        </p>
        {pct !== null ? (
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-zerqo-line">
            <div
              className={cn("h-full rounded-full", pct >= 100 ? "bg-red-500" : "bg-zerqo-orange")}
              style={{ width: `${pct}%` }}
            />
          </div>
        ) : null}
      </Card>

      <Card>
        <div className="flex items-center gap-2 text-zerqo-muted">
          <AlertTriangle className="size-4" />
          <span className="text-[13px] font-semibold">Escalations this month</span>
        </div>
        <p className="mt-3 text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">
          {stats.escalations_this_month}
        </p>
      </Card>
    </div>
  );
}

function RecentCallRow({ call }: { call: RecentCall }) {
  return (
    <Link
      href={`/portal/calls/${call.id}`}
      className="group flex items-start justify-between gap-4 rounded-xl px-3 py-3 transition-colors hover:bg-zerqo-cream/60"
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium tabular-nums text-zerqo-ink">
            {maskPhone(call.from_number)}
          </span>
          {call.outcome ? (
            <span className="rounded-full bg-zerqo-orange-soft px-2 py-0.5 text-[11px] font-medium text-zerqo-orange">
              {OUTCOME_LABEL[call.outcome] ?? call.outcome}
            </span>
          ) : null}
        </div>
        {call.summary ? (
          <p className="mt-0.5 truncate text-[13px] text-zerqo-muted">{call.summary}</p>
        ) : null}
      </div>
      <div className="shrink-0 text-right text-[12px] text-zerqo-muted">
        <p>{formatDateTime(call.started_at)}</p>
        <p className="tabular-nums">{formatDuration(call.duration_secs)}</p>
      </div>
    </Link>
  );
}

function RecentCalls({ calls }: { calls: RecentCall[] }) {
  return (
    <Card className="flex flex-col">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">Recent calls</h2>
        <Link
          href="/portal/calls"
          className="flex items-center gap-1 text-[13px] font-medium text-zerqo-orange hover:underline"
        >
          View all <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
      {calls.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center py-10 text-center">
          <Phone className="size-6 text-zerqo-muted" />
          <p className="mt-3 text-sm font-medium text-zerqo-ink">No calls yet</p>
          <p className="mt-1 max-w-xs text-[13px] text-zerqo-muted">
            Calls will appear here once your agent starts answering.
          </p>
        </div>
      ) : (
        <div className="-mx-3 divide-y divide-zerqo-line">
          {calls.map((call) => (
            <RecentCallRow key={call.id} call={call} />
          ))}
        </div>
      )}
    </Card>
  );
}

function ChartCard({ points }: { points: DashboardSummary["calls_over_time"] }) {
  const total = points.reduce((sum, p) => sum + p.count, 0);
  return (
    <Card>
      <div className="mb-5 flex items-baseline justify-between">
        <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">Calls over time</h2>
        <span className="text-[13px] text-zerqo-muted">Last 14 days</span>
      </div>
      {total === 0 ? (
        <div className="flex h-40 flex-col items-center justify-center text-center">
          <p className="text-sm font-medium text-zerqo-ink">No calls in the last 14 days</p>
          <p className="mt-1 text-[13px] text-zerqo-muted">
            Your activity chart will fill in here.
          </p>
        </div>
      ) : (
        <CallsChart points={points} />
      )}
    </Card>
  );
}

function KnowledgeCard({ knowledge }: { knowledge: DashboardSummary["knowledge"] }) {
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">Knowledge</h2>
        <Link
          href="/portal/knowledge"
          className="flex items-center gap-1 text-[13px] font-medium text-zerqo-orange hover:underline"
        >
          Manage <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
      {knowledge.document_count === 0 ? (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <BookOpen className="size-6 text-zerqo-muted" />
          <p className="mt-3 text-sm font-medium text-zerqo-ink">No documents yet</p>
          <p className="mt-1 max-w-xs text-[13px] text-zerqo-muted">
            Upload PDFs so your agent can answer from your own content.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-3xl font-bold tabular-nums tracking-tight text-zerqo-ink">
            {knowledge.document_count}
            <span className="ml-1 text-base font-medium text-zerqo-muted">
              document{knowledge.document_count === 1 ? "" : "s"}
            </span>
          </p>
          <p className="text-[13px] text-zerqo-muted">
            {knowledge.ready_count} of {knowledge.document_count} ready · last upload{" "}
            {formatDate(knowledge.last_upload)}
          </p>
        </div>
      )}
    </Card>
  );
}

function PlanCard({
  plan,
  businessName,
}: {
  plan: DashboardSummary["plan"];
  businessName: string;
}) {
  const renewHref = `mailto:sales@zerqo.com?subject=${encodeURIComponent(
    `Renew plan — ${businessName}`
  )}`;

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

function ErrorState({ businessName }: { businessName: string }) {
  return (
    <div className="space-y-8">
      <SectionLabel>Dashboard</SectionLabel>
      <Card>
        <h2 className="text-lg font-semibold tracking-tight text-zerqo-ink">
          We couldn&rsquo;t load your dashboard
        </h2>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-zerqo-muted">
          {businessName}&rsquo;s overview is temporarily unavailable. Please refresh the page — if
          this keeps happening, contact support.
        </p>
      </Card>
    </div>
  );
}

export function PortalDashboardContent({
  summary,
  displayName,
  businessName,
}: PortalDashboardContentProps) {
  if (!summary) {
    return <ErrorState businessName={businessName} />;
  }

  return (
    <div className="space-y-8">
      <div>
        <SectionLabel>Dashboard</SectionLabel>
        <h1 className="text-[clamp(28px,4vw,40px)] font-semibold leading-tight tracking-tight text-zerqo-ink">
          Welcome back, {displayName}
        </h1>
        <p className="mt-2 max-w-lg text-[15px] leading-relaxed text-zerqo-muted">
          Here&rsquo;s how {businessName} is doing.
        </p>
      </div>

      <StatTiles stats={summary.stats} />

      <OutboundCallCard />

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <ChartCard points={summary.calls_over_time} />
        <RecentCalls calls={summary.recent_calls} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <KnowledgeCard knowledge={summary.knowledge} />
        <PlanCard plan={summary.plan} businessName={businessName} />
      </div>
    </div>
  );
}
