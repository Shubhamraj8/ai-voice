import { cn } from "@/lib/utils";
import { formatShortDate } from "@/lib/format";
import type { CallPoint } from "@/lib/api/portal";

/**
 * Dependency-free, responsive bar chart for the 14-day calls series. Bars flex
 * to fill the width (mobile-friendly); native title tooltips show per-day counts.
 */
export function CallsChart({ points }: { points: CallPoint[] }) {
  const max = Math.max(1, ...points.map((p) => p.count));

  return (
    <div>
      <div
        className="flex h-40 items-end gap-[3px]"
        role="img"
        aria-label="Calls over the last 14 days"
      >
        {points.map((p) => {
          const pct = p.count > 0 ? Math.max((p.count / max) * 100, 6) : 0;
          return (
            <div key={p.date} className="group flex flex-1 items-end self-stretch">
              <div
                className={cn(
                  "w-full rounded-t-sm transition-colors",
                  p.count > 0 ? "bg-zerqo-orange/85 group-hover:bg-zerqo-orange" : "bg-zerqo-line"
                )}
                style={{ height: p.count > 0 ? `${pct}%` : "2px" }}
                title={`${formatShortDate(p.date)} · ${p.count} call${p.count === 1 ? "" : "s"}`}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-[11px] text-zerqo-muted">
        <span>{formatShortDate(points[0]?.date)}</span>
        <span>{formatShortDate(points[points.length - 1]?.date)}</span>
      </div>
    </div>
  );
}
