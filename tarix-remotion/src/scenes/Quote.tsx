import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { fonts } from "../fonts";
import type { QuoteProps } from "../schema";
import { Backdrop, Ornament, RevealText, Vignette, progress, useExit, useTheme } from "../components/ui";

export const Quote: React.FC<QuoteProps> = ({ text, author, source }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const exit = useExit(15);
  const words = text.split(" ").length;
  const size = words <= 6 ? 110 : words <= 18 ? 76 : 56;
  const authorAt = 20 + words * 4 + 10;

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      <Backdrop seed="quote" glow={[50, 40]} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 220px" }}>
        <div
          style={{
            position: "absolute",
            top: 120,
            left: 170,
            fontFamily: fonts.serif,
            fontSize: 420,
            lineHeight: 1,
            color: t.accent,
            opacity: 0.25 * progress(frame, 0, 30),
            transform: `translateY(${interpolate(progress(frame, 0, 30), [0, 1], [-40, 0])}px)`,
          }}
        >
          “
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 50 }}>
          <RevealText
            text={text}
            delay={20}
            stagger={4}
            style={{
              fontFamily: fonts.serifItalic,
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: size,
              lineHeight: 1.25,
              color: t.text,
              textAlign: "center",
              justifyContent: "center",
            }}
          />
          <Ornament width={420} delay={authorAt - 10} />
          <div style={{ textAlign: "center", opacity: progress(frame, authorAt, 25) }}>
            <div style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 40, letterSpacing: 6, color: t.accent }}>
              {author}
            </div>
            <div style={{ fontFamily: fonts.sans, fontSize: 22, color: t.paper, opacity: 0.7, marginTop: 8 }}>{source}</div>
          </div>
        </div>
      </AbsoluteFill>
      <Vignette />
    </AbsoluteFill>
  );
};
