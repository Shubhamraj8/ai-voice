export default function BillingLoading() {
  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
        </div>
        <div className="h-8 w-32 animate-pulse rounded bg-zerqo-line" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="h-64 animate-pulse rounded-2xl border border-zerqo-line bg-white shadow-sm" />
        <div className="h-64 animate-pulse rounded-2xl border border-zerqo-line bg-white shadow-sm" />
      </div>
      <div className="h-48 animate-pulse rounded-2xl border border-zerqo-line bg-white shadow-sm" />
    </div>
  );
}
