export function PortalWaveMark({ size = 34 }: { size?: number }) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-[9px] bg-zerqo-black shadow-[0_0_24px_rgba(240,78,0,0.35)]"
      style={{ width: size, height: size }}
    >
      <svg width={size * 0.58} height={size * 0.4} viewBox="0 0 20 14">
        {[6, 10, 14, 10, 6].map((h, i) => (
          <rect
            key={i}
            x={i * 4 + 1.5}
            y={(14 - h) / 2}
            width="2.5"
            height={h}
            rx="1.25"
            fill="#fff"
          />
        ))}
      </svg>
    </div>
  );
}
