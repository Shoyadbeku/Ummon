// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — film-burn.tsx (used as a light-leak transition overlay)
import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

export const FilmBurn: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const intensity = interpolate(frame, [0, durationInFrames * 0.5, durationInFrames], [0, 0.85, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const x1 = 50 + Math.sin(frame * 0.05) * 30, y1 = 50 + Math.cos(frame * 0.04) * 20;
  const x2 = 50 + Math.sin(frame * 0.07 + 2) * 25, y2 = 50 + Math.cos(frame * 0.06 + 1) * 30;
  const x3 = 50 + Math.sin(frame * 0.03 + 4) * 20, y3 = 50 + Math.cos(frame * 0.08 + 3) * 15;
  const layer = (bg: string): React.CSSProperties => ({
    position: "absolute", inset: 0, background: bg, mixBlendMode: "screen",
  });
  return (
    <>
      <div style={layer(`radial-gradient(circle at ${x1}% ${y1}%, rgba(249,115,22,${intensity * 0.7}), transparent 60%)`)} />
      <div style={layer(`radial-gradient(circle at ${x2}% ${y2}%, rgba(251,191,36,${intensity * 0.5}), transparent 50%)`)} />
      <div style={layer(`radial-gradient(circle at ${x3}% ${y3}%, rgba(255,255,255,${intensity * 0.3}), transparent 40%)`)} />
    </>
  );
};
