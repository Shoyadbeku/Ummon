// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — noise-grain.tsx + vignette-pulse.tsx
// Grain cycles 8 pre-generated noise tiles instead of thousands of <rect>s
// so 12-minute renders stay fast.
import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export const FilmGrain: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const vignette = 0.62 + 0.08 * Math.sin((frame / fps) * Math.PI * 0.25);
  const flicker = 0.03 * Math.sin(frame * 1.7) * Math.sin(frame * 0.37);
  return (
    <>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${vignette}) 100%)`,
        }}
      />
      <div style={{ position: "absolute", inset: 0, backgroundColor: "rgba(255,240,210,1)", opacity: 0.03 + flicker, mixBlendMode: "overlay" }} />
      <Img
        src={staticFile(`grain/g${frame % 8}.png`)}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.1, mixBlendMode: "overlay", transform: `translate(${(frame * 37) % 7}px, ${(frame * 53) % 5}px) scale(1.02)` }}
      />
    </>
  );
};
