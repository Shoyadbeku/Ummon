// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — ken-burns.tsx
// (rewritten with useCurrentFrame/interpolate so it renders deterministically)
import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame, Easing } from "remotion";

export const KenBurns: React.FC<{
  src: string;
  durationInFrames: number;
  variant: number;
}> = ({ src, durationInFrames, variant }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });
  // 6 camera moves: zoom-in, zoom-out, pan L→R, pan R→L, pan up, diagonal
  const moves = [
    { s: [1.05, 1.25], x: [0, -2], y: [0, -1] },
    { s: [1.28, 1.06], x: [-2, 1], y: [-1, 0] },
    { s: [1.18, 1.2], x: [4, -4], y: [0, 0] },
    { s: [1.2, 1.18], x: [-4, 4], y: [1, -1] },
    { s: [1.15, 1.22], x: [0, 0], y: [3, -3] },
    { s: [1.08, 1.24], x: [3, -3], y: [2, -2] },
  ];
  const m = moves[variant % moves.length];
  const scale = m.s[0] + (m.s[1] - m.s[0]) * p;
  const tx = m.x[0] + (m.x[1] - m.x[0]) * p;
  const ty = m.y[0] + (m.y[1] - m.y[0]) * p;
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", backgroundColor: "black" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${tx}%, ${ty}%)`,
          filter: "sepia(0.18) contrast(1.08) saturate(0.9) brightness(0.92)",
        }}
      />
    </div>
  );
};
