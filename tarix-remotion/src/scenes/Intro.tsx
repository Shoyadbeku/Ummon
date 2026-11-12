import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fonts } from "../fonts";
import type { IntroProps } from "../schema";
import {
  Backdrop,
  FrameCorners,
  KenBurns,
  Kicker,
  Ornament,
  RevealText,
  Vignette,
  progress,
  useExit,
  useTheme,
} from "../components/ui";

export const Intro: React.FC<IntroProps> = ({ kicker, title, subtitle, yearFrom, yearTo, image }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = useExit(20);

  // Large background year counts from start to end over the scene
  const year = Math.round(
    interpolate(frame, [10, durationInFrames * 0.75], [yearFrom, yearTo], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const titleP = progress(frame, 18, 40);
  const letterSpacing = interpolate(titleP, [0, 1], [60, 14]);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {image ? (
        <>
          <KenBurns src={image} zoom="in" />
          <AbsoluteFill style={{ background: `${t.background}c0` }} />
        </>
      ) : (
        <Backdrop seed="intro" />
      )}

      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            position: "absolute",
            fontFamily: fonts.display,
            fontWeight: 700,
            fontSize: 520,
            color: "transparent",
            WebkitTextStroke: `2px ${t.accent}`,
            opacity: 0.12 * progress(frame, 0, 30),
            letterSpacing: 10,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {year}
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 28 }}>
          <Kicker delay={5}>{kicker}</Kicker>
          <Ornament width={700} delay={10} />
          <div
            style={{
              fontFamily: fonts.display,
              fontWeight: 700,
              fontSize: 150,
              color: t.text,
              letterSpacing,
              opacity: titleP,
              filter: `blur(${(1 - titleP) * 16}px)`,
              textShadow: `0 0 60px ${t.accent}55`,
              textTransform: "uppercase",
              textAlign: "center",
              lineHeight: 1,
            }}
          >
            {title}
          </div>
          <Ornament width={700} delay={30} />
          <RevealText
            text={subtitle}
            delay={45}
            style={{
              fontFamily: fonts.serifItalic,
              fontStyle: "italic",
              fontSize: 48,
              color: t.paper,
              justifyContent: "center",
            }}
          />
          <div
            style={{
              fontFamily: fonts.sans,
              fontSize: 24,
              letterSpacing: 6,
              color: t.text,
              opacity: 0.7 * progress(frame, 60, 25),
            }}
          >
            {yearFrom} — {yearTo}
          </div>
        </div>
      </AbsoluteFill>
      <FrameCorners delay={20} />
      <Vignette />
    </AbsoluteFill>
  );
};
