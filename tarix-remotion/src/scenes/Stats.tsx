import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fonts } from "../fonts";
import type { StatsProps } from "../schema";
import { Backdrop, Kicker, Ornament, Vignette, progress, useExit, useTheme } from "../components/ui";

const decimals = (v: number) => (String(v).split(".")[1] ?? "").length;
const fmt = (v: number, d: number) =>
  v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }).replace(/,/g, " ");

export const Stats: React.FC<StatsProps> = ({ title, stats }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const exit = useExit(15);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <Backdrop seed="stats" glow={[50, 55]} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 70 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
          <Kicker>{title}</Kicker>
          <Ornament width={500} delay={5} />
        </div>
        <div style={{ display: "flex", gap: 0 }}>
          {stats.map((s, i) => {
            const delay = 15 + i * 12;
            const p = progress(frame, delay, 25);
            const count = interpolate(frame, [delay, delay + 50], [0, s.value], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: (x) => 1 - Math.pow(1 - x, 3),
            });
            return (
              <div
                key={i}
                style={{
                  width: 1500 / Math.max(1, stats.length),
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 16,
                  borderLeft: i === 0 ? "none" : `1px solid ${t.accent}55`,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 40}px)`,
                }}
              >
                <div
                  style={{
                    fontFamily: fonts.display,
                    fontWeight: 700,
                    fontSize: 120,
                    color: t.text,
                    lineHeight: 1,
                    fontVariantNumeric: "tabular-nums",
                    whiteSpace: "nowrap",
                  }}
                >
                  <span style={{ color: t.accent }}>{s.prefix}</span>
                  {fmt(count, decimals(s.value))}
                </div>
                <div style={{ fontFamily: fonts.serif, fontWeight: 600, fontSize: 40, color: t.accent }}>{s.suffix.trim()}</div>
                <div
                  style={{
                    fontFamily: fonts.sans,
                    fontSize: 24,
                    letterSpacing: 5,
                    textTransform: "uppercase",
                    color: t.paper,
                    opacity: 0.8,
                  }}
                >
                  {s.label}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <Vignette />
    </AbsoluteFill>
  );
};
