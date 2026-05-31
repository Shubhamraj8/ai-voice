import { getInternalNavItem } from "./nav";

type InternalPlaceholderPageProps = {
  href: string;
};

export function InternalPlaceholderPage({ href }: InternalPlaceholderPageProps) {
  const item = getInternalNavItem(href);
  const Icon = item.icon;

  return (
    <div className="space-y-10">
      <div>
        <div className="mb-5 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">{item.label}</span>
        </div>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-3">
            <h1 className="text-[clamp(28px,4vw,40px)] font-semibold leading-tight tracking-tight text-zerqo-ink">
              {item.label}
            </h1>
            <p className="max-w-lg text-[15px] leading-relaxed text-zerqo-muted">
              {item.description}
            </p>
          </div>
          <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-zerqo-orange text-white shadow-md">
            <Icon className="size-5" />
          </span>
        </div>
      </div>

      {item.previewStats ? (
        <div className="overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm">
          <div className="grid sm:grid-cols-3">
            {item.previewStats.map((stat, i) => (
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
      ) : null}

      <div className="rounded-2xl border border-zerqo-line bg-white p-8 shadow-sm">
        <p className="font-mono text-xs font-medium text-zerqo-orange">Phase 3</p>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-zerqo-ink">
          Coming in the next release
        </h2>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-zerqo-muted">
          The internal shell is live — auth, navigation, and role guards are wired. Data for{" "}
          {item.label.toLowerCase()} connects when Phase 3 ships.
        </p>
        <div className="mt-6 h-px bg-zerqo-line" />
        <ul className="mt-5 space-y-2.5">
          {["Role-based access enforced", "Cross-tenant views reserved", "API hooks ready"].map(
            (line) => (
              <li key={line} className="flex items-center gap-2.5 text-[13px] text-zerqo-muted">
                <span className="flex size-4 shrink-0 items-center justify-center rounded-full bg-zerqo-orange-soft">
                  <span className="size-1.5 rounded-full bg-zerqo-orange" />
                </span>
                {line}
              </li>
            )
          )}
        </ul>
      </div>
    </div>
  );
}
