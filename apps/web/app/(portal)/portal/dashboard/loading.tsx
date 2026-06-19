function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm ${className}`}
    >
      <div className="h-3 w-24 rounded bg-zerqo-line" />
      <div className="mt-4 h-8 w-20 rounded bg-zerqo-line" />
    </div>
  );
}

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div>
        <div className="mb-5 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Dashboard</span>
        </div>
        <div className="h-9 w-64 animate-pulse rounded bg-zerqo-line" />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <SkeletonCard className="h-64" />
        <SkeletonCard className="h-64" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <SkeletonCard className="h-40" />
        <SkeletonCard className="h-40" />
      </div>
    </div>
  );
}
