export default function CallsLoading() {
  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
        </div>
        <div className="h-8 w-28 animate-pulse rounded bg-zerqo-line" />
      </div>

      <div className="h-28 animate-pulse rounded-2xl border border-zerqo-line bg-white shadow-sm" />

      <div className="overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="border-b border-zerqo-line px-5 py-4 last:border-b-0">
            <div className="h-4 w-full animate-pulse rounded bg-zerqo-line" />
          </div>
        ))}
      </div>
    </div>
  );
}
