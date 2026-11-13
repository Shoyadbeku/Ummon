// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — stat-counter.tsx
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, TITLE } from "../fonts";

export const StatCounter: React.FC<{ value: number; suffix?: string; label: string; durationInFrames: number }> = ({
  value, suffix = "", label, durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const count = Math.round(interpolate(frame, [10, 60], [0, value], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const labelOpacity = interpolate(frame, [30, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 120, right: 110, opacity: out, transform: `scale(${scale})`, transformOrigin: "top right" }}>
      <div style={{ background: "rgba(10,8,5,0.6)", border: `1px solid ${GOLD}55`, padding: "30px 56px", textAlign: "center", boxShadow: "0 10px 40px rgba(0,0,0,0.5)" }}>
        <div style={{ fontFamily: TITLE, fontSize: 120, fontWeight: 700, color: "#f5ead2", lineHeight: 1, textShadow: "0 4px 10px rgba(0,0,0,0.5)" }}>
          {count.toLocaleString("en-US").replace(/,/g, " ")}{suffix}
        </div>
        <div style={{ fontFamily: SERIF, fontStyle: "italic", fontSize: 34, color: GOLD, marginTop: 12, opacity: labelOpacity }}>{label}</div>
      </div>
    </div>
  );
};
