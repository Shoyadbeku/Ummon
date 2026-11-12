import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fonts } from "../fonts";
import type { ImageProps } from "../schema";
import { KenBurns, Vignette, progress, useExit, useTheme } from "../components/ui";

/** Full-bleed archival image with Ken Burns motion and a lower-third caption. */
export const ImageScene: React.FC<ImageProps> = ({ image, caption, place, date, credit, zoom, pan }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const exit = useExit(15);
  const bar = progress(frame, 15, 25);
  const txt = progress(frame, 25, 25);

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <KenBurns src={image} zoom={zoom} pan={pan} label={image ? undefined : "RASM UCHUN JOY"} />
      <AbsoluteFill
        style={{ background: "linear-gradient(0deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 45%)" }}
      />

      {/* date stamp, top-left */}
      <div
        style={{
          position: "absolute",
          top: 70,
          left: 90,
          padding: "10px 22px",
          border: `2px solid ${t.accent}`,
          fontFamily: fonts.display,
          fontSize: 30,
          color: t.text,
          letterSpacing: 4,
          background: "rgba(0,0,0,0.35)",
          opacity: progress(frame, 5, 20),
          transform: `translateY(${(1 - progress(frame, 5, 20)) * -20}px)`,
        }}
      >
        {date}
      </div>

      {/* lower third */}
      <div style={{ position: "absolute", left: 90, bottom: 110, display: "flex", gap: 28 }}>
        <div style={{ width: 6, background: t.accent, transform: `scaleY(${bar})`, transformOrigin: "bottom" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 6, overflow: "hidden" }}>
          <div
            style={{
              fontFamily: fonts.sans,
              fontWeight: 600,
              fontSize: 26,
              letterSpacing: 8,
              color: t.accent,
              textTransform: "uppercase",
              opacity: txt,
            }}
          >
            {place}
          </div>
          <div
            style={{
              fontFamily: fonts.serif,
              fontWeight: 700,
              fontSize: 76,
              color: t.text,
              transform: `translateX(${interpolate(txt, [0, 1], [-40, 0])}px)`,
              opacity: txt,
            }}
          >
            {caption}
          </div>
        </div>
      </div>

      {credit ? (
        <div
          style={{
            position: "absolute",
            right: 60,
            bottom: 40,
            fontFamily: fonts.sans,
            fontSize: 18,
            color: t.paper,
            opacity: 0.6 * progress(frame, 40, 20),
          }}
        >
          {credit}
        </div>
      ) : null}
      <Vignette strength={0.6} />
    </AbsoluteFill>
  );
};
