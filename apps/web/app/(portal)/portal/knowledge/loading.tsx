export default function KnowledgeLoading() {
  return (
    <div className="space-y-6">
      <div>
        <div className="mb-3 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Client portal</span>
        </div>
        <div className="h-8 w-36 animate-pulse rounded bg-zerqo-line" />
      </div>
      <div className="h-48 animate-pulse rounded-2xl border border-zerqo-line bg-white shadow-sm" />
    </div>
  );
}
