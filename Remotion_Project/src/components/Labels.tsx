import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT, FONT } from "../theme";

/** Small factual caption for what is on screen (place / date / document). */
export const ShotTag: React.FC<{ label: string | null }> = ({ label }) => {
  const frame = useCurrentFrame();
  if (!label) return null;
  const o = interpolate(frame, [8, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const x = interpolate(frame, [8, 24], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute", top: 64, left: 72, opacity: o, transform: `translateX(${x}px)`,
        display: "flex", alignItems: "center", gap: 14, fontFamily: FONT,
      }}
    >
      <div style={{ width: 5, height: 34, background: ACCENT }} />
      <div
        style={{
          color: "#fff", fontSize: 27, fontWeight: 600, letterSpacing: 0.3,
          background: "rgba(0,0,0,0.55)", padding: "6px 14px", borderRadius: 3,
          textShadow: "0 1px 3px rgba(0,0,0,0.8)", maxWidth: 1100,
        }}
      >
        {label}
      </div>
    </div>
  );
};

/** Source attribution, always visible top-right while a shot is on screen. */
export const SourceCredit: React.FC<{ credit: string; kind: string }> = ({ credit, kind }) => {
  const tag = kind === "archive" ? "ARXIV" : kind === "interview" ? "INTERVYU" : kind === "location" ? "JOY" : "MANBA";
  return (
    <div
      style={{
        position: "absolute", top: 66, right: 72, fontFamily: FONT, fontSize: 19, color: "rgba(255,255,255,0.82)",
        letterSpacing: 1.2, textShadow: "0 1px 3px rgba(0,0,0,0.9)", textAlign: "right",
      }}
    >
      <span style={{ color: ACCENT, fontWeight: 700 }}>{tag}</span>
      <span style={{ opacity: 0.6 }}> • </span>
      {credit}
    </div>
  );
};

/** Documentary lower-third with name + role. */
export const LowerThird: React.FC<{ name: string; role: string; duration: number }> = ({ name, role, duration }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inP = spring({ frame: frame - 6, fps, config: { damping: 200 } });
  const out = interpolate(frame, [duration - 14, duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bar = interpolate(inP, [0, 1], [0, 1]);
  return (
    <div style={{ position: "absolute", left: 96, bottom: 210, opacity: out, fontFamily: FONT }}>
      <div style={{ height: 4, width: 340 * bar, background: ACCENT, marginBottom: 12 }} />
      <div style={{ overflow: "hidden" }}>
        <div
          style={{
            transform: `translateY(${(1 - inP) * 60}px)`, color: "#fff", fontSize: 50, fontWeight: 800,
            letterSpacing: 0.5, textShadow: "0 2px 10px rgba(0,0,0,0.8)",
          }}
        >
          {name}
        </div>
      </div>
      <div style={{ overflow: "hidden" }}>
        <div
          style={{
            transform: `translateY(${(1 - spring({ frame: frame - 12, fps, config: { damping: 200 } })) * 40}px)`,
            color: "rgba(255,255,255,0.88)", fontSize: 28, fontWeight: 500, marginTop: 4,
            textShadow: "0 2px 8px rgba(0,0,0,0.85)",
          }}
        >
          {role}
        </div>
      </div>
    </div>
  );
};
