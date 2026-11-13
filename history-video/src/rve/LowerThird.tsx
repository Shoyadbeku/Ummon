// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — lower-third.tsx
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, TITLE } from "../fonts";

export const LowerThird: React.FC<{ name: string; role: string; durationInFrames: number }> = ({ name, role, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const accent = spring({ frame, fps, from: -400, to: 0, durationInFrames: 25, config: { damping: 15, mass: 0.6 } });
  const bar = spring({ frame: Math.max(0, frame - 5), fps, from: -700, to: 0, durationInFrames: 30, config: { damping: 14, mass: 0.7 } });
  const text = spring({ frame: Math.max(0, frame - 15), fps, from: 0, to: 1, durationInFrames: 20 });
  const out = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 150, left: 90, opacity: out }}>
      <div style={{ width: 260, height: 3, background: `linear-gradient(90deg, ${GOLD}, transparent)`, transform: `translateX(${accent}px)`, marginBottom: 6 }} />
      <div style={{ display: "flex", transform: `translateX(${bar}px)` }}>
        <div style={{ width: 6, background: GOLD }} />
        <div style={{ background: "linear-gradient(90deg, rgba(10,8,5,0.85), rgba(10,8,5,0.55))", padding: "20px 40px" }}>
          <div style={{ color: "#f5ead2", fontFamily: TITLE, fontSize: 46, fontWeight: 700, opacity: text, letterSpacing: "0.04em" }}>{name}</div>
          <div style={{ color: "rgba(234,223,200,0.8)", fontFamily: SERIF, fontStyle: "italic", fontSize: 30, opacity: text, marginTop: 6 }}>{role}</div>
        </div>
      </div>
    </div>
  );
};
