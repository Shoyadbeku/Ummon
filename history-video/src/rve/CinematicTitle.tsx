// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — cinematic-title-intro.tsx
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, TITLE } from "../fonts";

export const CinematicTitle: React.FC<{ title: string; subtitle: string; durationInFrames: number }> = ({
  title, subtitle, durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const titleY = spring({ frame, fps, from: 50, to: 0, durationInFrames: 40, config: { damping: 14, mass: 0.8 } });
  const titleOpacity = spring({ frame, fps, from: 0, to: 1, durationInFrames: 30 });
  const underline = interpolate(frame, [20, 50], [0, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const spacing = interpolate(frame, [0, durationInFrames], [0.18, 0.28]);
  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", opacity: out, background: "radial-gradient(ellipse at center, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 70%)" }}>
      <h1 style={{ color: "#f5ead2", fontFamily: TITLE, fontSize: 150, fontWeight: 700, opacity: titleOpacity, transform: `translateY(${titleY}px)`, margin: 0, letterSpacing: `${spacing}em`, textShadow: "0 6px 30px rgba(0,0,0,0.9)" }}>
        {title}
      </h1>
      <div style={{ width: `${underline}%`, maxWidth: 620, height: 3, background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`, marginTop: 18 }} />
      <p style={{ color: GOLD, fontFamily: SERIF, fontStyle: "italic", fontSize: 46, opacity: subOpacity, marginTop: 26, letterSpacing: "0.08em", textShadow: "0 3px 14px rgba(0,0,0,0.9)" }}>
        {subtitle}
      </p>
    </div>
  );
};
