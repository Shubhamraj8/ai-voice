// @ts-nocheck
"use client";

export function WaveMark({ dark = false }) {
  return (
    <div
      style={{
        width: 34,
        height: 34,
        background: dark ? "#1E1E1E" : "#0D0D0D",
        borderRadius: 9,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg width="20" height="14" viewBox="0 0 20 14">
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
