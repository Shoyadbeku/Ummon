import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { fonts } from "../fonts";
import type { TimelineProps } from "../schema";
import { Backdrop, Kicker, Vignette, progress, useExit, useTheme } from "../components/ui";

const GAP = 420; // px between events

/** Horizontal timeline; the camera glides along as events appear one by one. */
export const Timeline: React.FC<TimelineProps> = ({ title, events }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();
  const exit = useExit(15);
  const n = Math.max(1, events.length);
  const start = 20;
  const per = (durationInFrames - start - 30) / n;
  const lineY = 600;

  // Focus position (fractional event index) – eased step per event
  const focus = events.reduce((acc, _, i) => acc + progress(frame, start + i * per, per * 0.6), 0) - 1;
  const trackW = (n - 1) * GAP;
  const fitsOnScreen = trackW < width - 360;
  const margin = 300;
  const offset = fitsOnScreen
    ? (width - trackW) / 2
    : Math.max(width - margin - trackW, Math.min(margin, width / 2 - Math.max(0, focus) * GAP));
  const lineP = progress(frame, 5, 40);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <Backdrop seed="timeline" glow={[50, 60]} />
      <div style={{ position: "absolute", top: 70, left: 90, display: "flex", flexDirection: "column", gap: 10 }}>
        <Kicker>Xronologiya</Kicker>
        <div style={{ fontFamily: fonts.serif, fontWeight: 700, fontSize: 72, color: t.text, opacity: progress(frame, 5, 25) }}>
          {title}
        </div>
      </div>

      {/* base line across screen */}
      <div
        style={{
          position: "absolute",
          top: lineY,
          left: 0,
          height: 2,
          width: width * lineP,
          background: `linear-gradient(90deg, transparent, ${t.accent}80 15%, ${t.accent}80 85%, transparent)`,
        }}
      />

      <AbsoluteFill
        style={{
          maskImage: "linear-gradient(90deg, transparent 0%, #000 12%, #000 88%, transparent 100%)",
          WebkitMaskImage: "linear-gradient(90deg, transparent 0%, #000 12%, #000 88%, transparent 100%)",
        }}
      >
      <div style={{ position: "absolute", top: 0, left: 0, transform: `translateX(${offset}px)` }}>
        {events.map((e, i) => {
          const p = progress(frame, start + i * per, 22);
          const isFocus = Math.abs(focus - i) < 0.5;
          const up = i % 2 === 0;
          const x = i * GAP;
          return (
            <div key={i} style={{ position: "absolute", left: x, top: 0 }}>
              {/* marker */}
              <div
                style={{
                  position: "absolute",
                  left: -14,
                  top: lineY - 13,
                  width: 28,
                  height: 28,
                  transform: `rotate(45deg) scale(${p})`,
                  border: `3px solid ${t.accent}`,
                  background: isFocus ? t.accent : t.background,
                  boxShadow: isFocus ? `0 0 30px ${t.accent}` : "none",
                }}
              />
              {/* stem */}
              <div
                style={{
                  position: "absolute",
                  left: -1,
                  top: up ? lineY - 30 - 60 * p : lineY + 30,
                  width: 2,
                  height: 60 * p,
                  background: t.accent,
                  opacity: 0.7,
                }}
              />
              {/* card */}
              <div
                style={{
                  position: "absolute",
                  left: -170,
                  width: 340,
                  top: up ? lineY - 330 : lineY + 100,
                  height: 230,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: up ? "flex-end" : "flex-start",
                  alignItems: "center",
                  textAlign: "center",
                  gap: 6,
                  opacity: p * (isFocus ? 1 : 0.55),
                  transform: `translateY(${(1 - p) * (up ? 30 : -30)}px) scale(${isFocus ? 1 : 0.94})`,
                }}
              >
                <div style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 64, color: t.accent, lineHeight: 1 }}>
                  {e.year}
                </div>
                <div style={{ fontFamily: fonts.serif, fontWeight: 700, fontSize: 40, color: t.text }}>{e.title}</div>
                <div style={{ fontFamily: fonts.sans, fontSize: 22, color: t.paper, opacity: 0.8, lineHeight: 1.35 }}>
                  {e.text}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      </AbsoluteFill>
      <Vignette />
    </AbsoluteFill>
  );
};
