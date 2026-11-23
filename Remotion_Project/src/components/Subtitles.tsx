import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT } from "../theme";

type Sub = { start: number; end: number; text: string };

/** Subtitles synced to the original narration timestamps.
 *  Hidden while a chapter card shows the same words as a title. */
export const Subtitles: React.FC<{ subs: Sub[]; scenes: any[] }> = ({ subs, scenes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  for (const sc of scenes) {
    const ch = sc.extras?.chapter;
    if (ch) {
      const len = sc.extras.chapter_len ?? 3.4;
      if (t >= sc.vFrom / fps && t < sc.vFrom / fps + len) return null;
    }
    if (sc.extras?.end_title && t > sc.vTo / fps - 6.5) return null;
  }
  const cur = subs.find((s) => t >= s.start && t < s.end + 0.15);
  if (!cur) return null;
  const f0 = cur.start * fps;
  const o = interpolate(frame, [f0, f0 + 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute", left: 0, right: 0, bottom: 70, display: "flex", justifyContent: "center",
        opacity: o, fontFamily: FONT,
      }}
    >
      <div
        style={{
          maxWidth: 1500, textAlign: "center", color: "#fff", fontSize: 42, fontWeight: 600, lineHeight: 1.3,
          padding: "10px 26px", background: "rgba(0,0,0,0.58)", borderRadius: 6,
          textShadow: "0 2px 4px rgba(0,0,0,0.9)",
        }}
      >
        {cur.text}
      </div>
    </div>
  );
};
