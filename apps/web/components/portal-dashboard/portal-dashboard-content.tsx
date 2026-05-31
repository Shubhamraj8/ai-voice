import type { MeResponse } from "@/lib/api/me";

type PortalDashboardContentProps = {
  me: MeResponse | null;
  fallbackName: string | null;
};

export function PortalDashboardContent({ me, fallbackName }: PortalDashboardContentProps) {
  const displayName = fallbackName?.trim() || me?.user.email?.split("@")[0] || "there";
  const businessName = me?.tenant.business_name ?? "Your workspace";
  const plan = me?.tenant.plan ?? "starter";

  return (
    <div className="space-y-10">
      <div>
        <div className="mb-5 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Dashboard</span>
        </div>
        <div className="space-y-3">
          <h1 className="text-[clamp(28px,4vw,40px)] font-semibold leading-tight tracking-tight text-zerqo-ink">
            Welcome back, {displayName}
          </h1>
          <p className="max-w-lg text-[15px] leading-relaxed text-zerqo-muted">
            {businessName} is on the <span className="capitalize">{plan}</span> plan. Your agent
            dashboard and call analytics will appear here in Phase 5.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm">
        <div className="grid sm:grid-cols-3">
          {[
            { label: "Calls this week", value: "—" },
            { label: "Active agents", value: "—" },
            { label: "Answer rate", value: "—" },
          ].map((stat, i) => (
            <div
              key={stat.label}
              className={`flex flex-col items-center px-6 py-8 text-center ${i > 0 ? "border-t border-zerqo-line sm:border-t-0 sm:border-l" : ""}`}
            >
              <span className="text-[1.75rem] font-bold tabular-nums tracking-tight text-zerqo-orange">
                {stat.value}
              </span>
              <span className="mt-2 text-[13px] font-semibold text-zerqo-ink">{stat.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-zerqo-line bg-white p-8 shadow-sm">
        <p className="font-mono text-xs font-medium text-zerqo-orange">Phase 5 · Coming soon</p>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-zerqo-ink">
          Your dashboard is being built
        </h2>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-zerqo-muted">
          Auth and workspace context are connected
          {me ? " via the /me API" : ""}. Agent configuration, call history, and live metrics ship
          in the next release.
        </p>
        {me ? (
          <div className="mt-6 rounded-xl border border-zerqo-line bg-zerqo-cream/60 p-4">
            <p className="font-mono text-[11px] uppercase tracking-wider text-zerqo-muted">
              Connected workspace
            </p>
            <p className="mt-2 text-sm font-medium text-zerqo-ink">{me.tenant.business_name}</p>
            <p className="text-xs text-zerqo-muted">
              {me.user.email} · {me.role}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
