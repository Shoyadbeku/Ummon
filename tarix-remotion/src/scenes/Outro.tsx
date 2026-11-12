import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fonts } from "../fonts";
import type { OutroProps } from "../schema";
import { Backdrop, Ornament, Vignette, progress, useSpring, useTheme } from "../components/ui";

/**
 * End screen. The two dashed boxes on the right mark where YouTube end-screen
 * elements (video / playlist) go — they're 20s max, so keep this scene ≥ 10s.
 */
export const Outro: React.FC<OutroProps> = ({ title, channel, cta, next }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const btn = useSpring(35, 12);
  const clickAt = 70;
  const press = interpolate(frame, [clickAt, clickAt + 4, clickAt + 10], [1, 0.92, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const subscribed = frame >= clickAt + 4;
  const ring = progress(frame, clickAt, fps * 0.8);

  return (
    <AbsoluteFill>
      <Backdrop seed="outro" glow={[30, 50]} />
      <div style={{ position: "absolute", left: 140, top: 0, bottom: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: 30 }}>
        <div style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 120, color: t.text, opacity: progress(frame, 0, 30) }}>
          {title}
        </div>
        <Ornament width={520} delay={10} />
        <div style={{ fontFamily: fonts.serifItalic, fontStyle: "italic", fontSize: 44, color: t.paper, opacity: progress(frame, 20, 25) }}>
          {channel}
        </div>
        <div style={{ position: "relative", marginTop: 20, alignSelf: "flex-start" }}>
          <div
            style={{
              position: "absolute",
              inset: -8,
              borderRadius: 14,
              border: `3px solid ${t.accent}`,
              opacity: 1 - ring,
              transform: `scale(${1 + ring * 0.3})`,
            }}
          />
          <div
            style={{
              transform: `scale(${btn * press})`,
              background: subscribed ? "#3a3026" : "#c4302b",
              color: "#fff",
              fontFamily: fonts.sans,
              fontWeight: 600,
              fontSize: 36,
              padding: "22px 50px",
              borderRadius: 10,
              letterSpacing: 1,
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            {subscribed ? "✓ " : ""}
            {cta}
          </div>
        </div>
        <div style={{ fontFamily: fonts.sans, fontSize: 26, color: t.accent, letterSpacing: 2, opacity: progress(frame, 90, 25), marginTop: 30 }}>
          {next}
        </div>
      </div>

      {/* YouTube end-screen element placeholders */}
      <div style={{ position: "absolute", right: 140, top: 0, bottom: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: 50 }}>
        {[0, 1].map((i) => {
          const p = progress(frame, 25 + i * 10, 30);
          return (
            <div
              key={i}
              style={{
                width: 640,
                height: 360,
                border: `2px dashed ${t.accent}aa`,
                borderRadius: 8,
                background: "rgba(0,0,0,0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: fonts.sans,
                fontSize: 22,
                letterSpacing: 4,
                color: t.paper,
                opacity: p * 0.8,
                transform: `translateX(${(1 - p) * 60}px)`,
              }}
            >
              {i === 0 ? "KEYINGI VIDEO" : "PLEYLIST"}
            </div>
          );
        })}
      </div>
      <Vignette strength={0.6} />
    </AbsoluteFill>
  );
};
