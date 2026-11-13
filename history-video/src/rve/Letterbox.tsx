// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — letterbox-reveal.tsx
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const Letterbox: React.FC<{ final?: number }> = ({ final = 7 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const h = interpolate(frame, [0, fps * 2.2], [50, final], { extrapolateRight: "clamp" });
  const bar: React.CSSProperties = { position: "absolute", left: 0, width: "100%", height: `${h}%`, backgroundColor: "#000" };
  return (
    <>
      <div style={{ ...bar, top: 0 }} />
      <div style={{ ...bar, bottom: 0 }} />
    </>
  );
};
