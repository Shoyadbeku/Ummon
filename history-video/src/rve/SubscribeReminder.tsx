// Adapted from the free Remotion templates by React Video Editor
// https://github.com/reactvideoeditor/remotion-templates (reactvideoeditor.com) — subscribe-reminder.tsx
import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF, TITLE } from "../fonts";

export const SubscribeReminder: React.FC<{ channel: string }> = ({ channel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const slide = spring({ frame: Math.max(frame - 10, 0), fps, config: { damping: 14, stiffness: 100 } });
  const y = interpolate(slide, [0, 1], [260, 0]);
  const bell = interpolate(Math.sin(frame * 0.15), [-1, 1], [1, 1.15]);
  const ring = Math.sin(frame * 0.6) * 14 * Math.max(0, Math.sin(frame * 0.05));
  return (
    <div style={{ position: "absolute", top: 120, left: 0, right: 0, display: "flex", justifyContent: "center", transform: `translateY(${-y}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 26, background: "rgba(10,8,5,0.8)", padding: "20px 44px 20px 22px", borderRadius: 999, border: `1px solid ${GOLD}66` }}>
        <div style={{ width: 88, height: 88, borderRadius: "50%", backgroundColor: "#c4302b", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${bell}) rotate(${ring}deg)` }}>
          <svg width="46" height="46" viewBox="0 0 24 24" fill="white"><path d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11a7 7 0 0 0-5.5-6.84V3a1.5 1.5 0 0 0-3 0v1.16A7 7 0 0 0 5 11v5l-2 2v1h18v-1z"/></svg>
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ color: "#f5ead2", fontFamily: TITLE, fontWeight: 700, fontSize: 48 }}>OBUNA BO'LING</span>
          <span style={{ color: GOLD, fontFamily: SERIF, fontStyle: "italic", fontSize: 32 }}>{channel}</span>
        </div>
      </div>
    </div>
  );
};
