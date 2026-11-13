// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — typewriter-subtitle.tsx
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { GOLD, TYPE } from "../fonts";

export const TypewriterDate: React.FC<{ text: string; place?: string; durationInFrames: number }> = ({ text, place, durationInFrames }) => {
  const frame = useCurrentFrame();
  const visible = Math.floor(interpolate(frame, [0, 40], [0, text.length], { extrapolateRight: "clamp" }));
  const placeOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", top: 130, left: 100, opacity: out, textShadow: "0 3px 12px rgba(0,0,0,0.95)" }}>
      <div style={{ fontFamily: TYPE, fontSize: 60, color: "#f5ead2" }}>
        {text.slice(0, visible)}
        <span style={{ color: GOLD, opacity: frame % 15 < 7 && visible < text.length + 6 ? 1 : 0 }}>▌</span>
      </div>
      {place ? <div style={{ fontFamily: TYPE, fontSize: 32, color: GOLD, marginTop: 6, opacity: placeOpacity, letterSpacing: "0.06em" }}>{place}</div> : null}
    </div>
  );
};
