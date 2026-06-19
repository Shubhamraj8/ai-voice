import { DataExportCard } from "@/components/portal-dashboard/settings/data-export-card";

export default function PortalSettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
        </div>
        <h1 className="text-[clamp(24px,3vw,32px)] font-semibold tracking-tight text-zerqo-ink">
          Settings
        </h1>
        <p className="mt-2 max-w-lg text-[15px] leading-relaxed text-zerqo-muted">
          Manage your workspace preferences and data.
        </p>
      </div>

      <div>
        <p className="mb-3 font-mono text-[11px] uppercase tracking-wider text-zerqo-muted">
          Privacy &amp; data
        </p>
        <DataExportCard />
      </div>
    </div>
  );
}
