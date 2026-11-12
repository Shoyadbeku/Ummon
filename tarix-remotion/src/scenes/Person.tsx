import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fonts } from "../fonts";
import type { PersonProps } from "../schema";
import { Backdrop, KenBurns, Kicker, Vignette, progress, useExit, useTheme } from "../components/ui";

/** Portrait plate on the left, name, years and key facts on the right. */
export const Person: React.FC<PersonProps> = ({ name, years, role, facts, image }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const exit = useExit(15);
  const plate = progress(frame, 0, 35);
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <Backdrop seed="person" glow={[25, 50]} />
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", padding: "0 150px", gap: 110 }}>
        {/* portrait */}
        <div
          style={{
            position: "relative",
            width: 560,
            height: 740,
            flexShrink: 0,
            opacity: plate,
            transform: `translateY(${(1 - plate) * 40}px)`,
          }}
        >
          <div style={{ position: "absolute", inset: -18, border: `2px solid ${t.accent}`, opacity: 0.6 }} />
          <div style={{ position: "absolute", inset: 0, overflow: "hidden", background: "#24190f" }}>
            {image ? (
              <KenBurns src={image} zoom="in" />
            ) : (
              <AbsoluteFill
                style={{
                  alignItems: "center",
                  justifyContent: "center",
                  background: `radial-gradient(ellipse at 50% 35%, ${t.accent}55, #1a120a 75%)`,
                }}
              >
                <svg viewBox="0 0 200 260" width="80%" style={{ position: "absolute", bottom: 0 }}>
                  <path
                    d="M100 30 c-30 0 -48 22 -48 52 c0 22 10 40 26 50 l-6 18 c-40 8 -66 30 -72 110 h200 c-6 -80 -32 -102 -72 -110 l-6 -18 c16 -10 26 -28 26 -50 c0 -30 -18 -52 -48 -52z"
                    fill="#0d0905"
                    opacity={0.85}
                  />
                </svg>
                <div
                  style={{
                    fontFamily: fonts.display,
                    fontSize: 120,
                    color: t.accent,
                    opacity: 0.35,
                    position: "absolute",
                    top: 60,
                  }}
                >
                  {initials}
                </div>
              </AbsoluteFill>
            )}
          </div>
          <div
            style={{
              position: "absolute",
              bottom: -30,
              left: "50%",
              transform: "translateX(-50%)",
              background: t.accent,
              color: t.background,
              fontFamily: fonts.display,
              fontWeight: 700,
              fontSize: 28,
              letterSpacing: 4,
              padding: "10px 30px",
              whiteSpace: "nowrap",
            }}
          >
            {years}
          </div>
        </div>

        {/* text */}
        <div style={{ display: "flex", flexDirection: "column", gap: 22, flex: 1 }}>
          <Kicker delay={10}>{role}</Kicker>
          <div
            style={{
              fontFamily: fonts.display,
              fontWeight: 700,
              fontSize: 110,
              lineHeight: 1,
              color: t.text,
              opacity: progress(frame, 15, 30),
              transform: `translateX(${interpolate(progress(frame, 15, 30), [0, 1], [-50, 0])}px)`,
            }}
          >
            {name}
          </div>
          <div
            style={{
              height: 2,
              width: 520 * progress(frame, 30, 30),
              background: `linear-gradient(90deg, ${t.accent}, transparent)`,
              margin: "10px 0",
            }}
          />
          {facts.map((f, i) => {
            const p = progress(frame, 45 + i * 22, 25);
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: 22,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 20}px)`,
                }}
              >
                <div style={{ width: 12, height: 12, background: t.accent, transform: "rotate(45deg)", flexShrink: 0 }} />
                <div style={{ fontFamily: fonts.serif, fontWeight: 600, fontSize: 42, color: t.paper, lineHeight: 1.25 }}>{f}</div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <Vignette />
    </AbsoluteFill>
  );
};
