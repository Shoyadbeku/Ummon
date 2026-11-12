import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fonts } from "../fonts";
import type { ChapterProps } from "../schema";
import { Backdrop, Ornament, RevealText, Vignette, progress, toRoman, useExit, useTheme } from "../components/ui";

export const Chapter: React.FC<ChapterProps> = ({ number, title, dates }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const exit = useExit(15);
  const numP = progress(frame, 0, 35);
  const wipe = progress(frame, 8, 30);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <Backdrop seed={`ch${number}`} glow={[30, 50]} />
      {/* gold light sweep */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(100deg, transparent 0%, ${t.accent}22 45%, transparent 55%)`,
          transform: `translateX(${interpolate(frame, [0, 60], [-100, 100], { extrapolateRight: "clamp" })}%)`,
        }}
      />
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", padding: "0 180px", gap: 90 }}>
        <div
          style={{
            fontFamily: fonts.display,
            fontWeight: 700,
            fontSize: 300,
            lineHeight: 1,
            color: "transparent",
            WebkitTextStroke: `3px ${t.accent}`,
            opacity: numP,
            transform: `scale(${interpolate(numP, [0, 1], [1.4, 1])})`,
            minWidth: 360,
            textAlign: "center",
          }}
        >
          {toRoman(number)}
        </div>
        <div
          style={{
            width: 3,
            height: 360 * wipe,
            background: `linear-gradient(180deg, transparent, ${t.accent}, transparent)`,
          }}
        />
        <div style={{ display: "flex", flexDirection: "column", gap: 24, flex: 1 }}>
          <div
            style={{
              fontFamily: fonts.sans,
              fontWeight: 600,
              fontSize: 26,
              letterSpacing: 10,
              color: t.accent,
              opacity: progress(frame, 10, 20),
            }}
          >
            {number}-BOB
          </div>
          <RevealText
            text={title}
            delay={14}
            stagger={5}
            style={{ fontFamily: fonts.serif, fontWeight: 700, fontSize: 96, lineHeight: 1.05, color: t.text }}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 24, opacity: progress(frame, 35, 20) }}>
            <Ornament width={160} delay={35} dur={20} />
            <div style={{ fontFamily: fonts.sans, fontSize: 30, letterSpacing: 4, color: t.paper }}>{dates}</div>
          </div>
        </div>
      </AbsoluteFill>
      <Vignette />
    </AbsoluteFill>
  );
};
