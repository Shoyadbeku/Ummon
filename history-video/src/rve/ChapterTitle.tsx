// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — chapter-title.tsx
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, TITLE } from "../fonts";

export const ChapterTitle: React.FC<{ label: string; number: string; title: string; durationInFrames: number }> = ({
  label, number, title, durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const numberScale = spring({ frame, fps, config: { damping: 12, stiffness: 80 } });
  const subOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const subY = interpolate(frame, [20, 40], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const line = interpolate(frame, [10, 40], [0, 180], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const labelOpacity = interpolate(frame, [5, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bg = interpolate(frame, [0, 12, durationInFrames - 15, durationInFrames], [0, 0.72, 0.72, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, backgroundColor: `rgba(8,6,4,${bg})`, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
      <div style={{ opacity: out, display: "flex", flexDirection: "column", alignItems: "center" }}>
        <p style={{ color: "#bfae8f", fontFamily: TITLE, fontSize: 30, letterSpacing: "0.35em", textTransform: "uppercase", margin: 0, marginBottom: 8, opacity: labelOpacity }}>{label}</p>
        <h1 style={{ color: "#f5ead2", fontFamily: TITLE, fontSize: 190, fontWeight: 700, margin: 0, lineHeight: 1, transform: `scale(${numberScale})` }}>{number}</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 18, marginTop: 28, marginBottom: 20 }}>
          <div style={{ height: 1, width: line, backgroundColor: GOLD }} />
          <div style={{ width: 9, height: 9, transform: "rotate(45deg)", backgroundColor: GOLD, opacity: labelOpacity }} />
          <div style={{ height: 1, width: line, backgroundColor: GOLD }} />
        </div>
        <p style={{ color: "#eadfc8", fontFamily: SERIF, fontStyle: "italic", fontSize: 54, margin: 0, letterSpacing: "0.04em", opacity: subOpacity, transform: `translateY(${subY}px)` }}>{title}</p>
      </div>
    </div>
  );
};
