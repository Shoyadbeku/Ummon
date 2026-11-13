// Word-synced captions, styled after RVE's text-highlight.tsx template.
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { GOLD, SERIF } from "./fonts";

export type Word = { w: string; s: number; e: number };
export type Chunk = { words: Word[]; from: number; to: number };

export const buildChunks = (scenes: { words: Word[] }[]): Chunk[] => {
  const chunks: Chunk[] = [];
  for (const sc of scenes) {
    let cur: Word[] = [];
    const flush = () => { if (cur.length) chunks.push({ words: cur, from: cur[0].s, to: 0 }); cur = []; };
    sc.words.forEach((w, i) => {
      cur.push(w);
      const chars = cur.map((x) => x.w).join(" ").length;
      const next = sc.words[i + 1];
      const sentenceEnd = /[.?!]$/.test(w.w) && cur.length >= 3;
      const pause = next && next.s - w.e > 0.6 && cur.length >= 2;
      if (cur.length >= 8 || chars > 46 || sentenceEnd || pause || (/[,—]$/.test(w.w) && chars > 30)) flush();
    });
    flush();
  }
  chunks.forEach((c, i) => {
    const last = c.words[c.words.length - 1].e + 0.6;
    c.to = i + 1 < chunks.length ? Math.min(chunks[i + 1].from, last) : last;
  });
  return chunks;
};

export const Subtitles: React.FC<{ chunks: Chunk[]; offset: number }> = ({ chunks, offset }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps - offset;
  const c = chunks.find((x) => t >= x.from - 0.05 && t < x.to);
  if (!c) return null;
  const opacity = interpolate(t, [c.from - 0.05, c.from + 0.1, c.to - 0.12, c.to], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 105, display: "flex", justifyContent: "center", opacity }}>
      <div style={{ maxWidth: 1500, textAlign: "center", padding: "10px 30px", background: "linear-gradient(90deg, transparent, rgba(0,0,0,0.45) 15%, rgba(0,0,0,0.45) 85%, transparent)" }}>
        {c.words.map((w, i) => {
          const active = t >= w.s && t < w.e + 0.08;
          const said = t >= w.s;
          return (
            <span key={i} style={{ fontFamily: SERIF, fontSize: 54, fontWeight: 600, color: active ? GOLD : said ? "#fbf6ea" : "rgba(251,246,234,0.72)", textShadow: "0 3px 10px rgba(0,0,0,0.95), 0 0 2px #000", marginRight: 14, display: "inline-block", transform: active ? "translateY(-2px)" : "none" }}>
              {w.w}
            </span>
          );
        })}
      </div>
    </div>
  );
};
