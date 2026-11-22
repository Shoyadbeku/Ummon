import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, MONT} from '../theme';

export type Word = {w: string; s: number; e: number; k?: 0 | 1 | 2};
// k: 0 normal, 1 keyword (green), 2 strong keyword (yellow + bigger)

type Page = {words: Word[]; start: number; end: number};

const MAX_CHARS = 20;
const MAX_WORDS = 4;

export const buildPages = (words: Word[]): Page[] => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) pages.push({words: cur, start: cur[0].s, end: cur[cur.length - 1].e});
    cur = [];
  };
  words.forEach((w, i) => {
    const prev = words[i - 1];
    const chars = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
    if (cur.length && (chars > MAX_CHARS || cur.length >= MAX_WORDS || (prev && w.s - prev.e > 0.45))) flush();
    cur.push(w);
    if (/[.!?…:;]$/.test(w.w) || (/,$/.test(w.w) && cur.length >= 2)) flush();
  });
  flush();
  // extend each page until the next one starts (max 0.6s hold) so text doesn't blink
  for (let i = 0; i < pages.length; i++) {
    const next = pages[i + 1];
    const hold = next ? Math.min(next.start, pages[i].end + 0.6) : pages[i].end + 0.8;
    pages[i].end = Math.max(pages[i].end, hold);
  }
  return pages;
};

export const Captions: React.FC<{words: Word[]; hidden?: [number, number][]}> = ({words, hidden = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const pages = useMemo(() => buildPages(words), [words]);
  if (hidden.some(([a, b]) => t >= a && t < b)) return null;
  const page = pages.find((p) => t >= p.start - 0.05 && t < p.end);
  if (!page) return null;

  const pageFrame = frame - Math.round(page.start * fps);
  const pop = spring({frame: pageFrame, fps, config: {damping: 14, stiffness: 220, mass: 0.6}});

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 70,
          right: 150, // right rail is covered by TikTok/Reels buttons
          top: 1170,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '4px 40px',
          transform: `translateX(40px) scale(${interpolate(pop, [0, 1], [0.82, 1])}) translateY(${interpolate(pop, [0, 1], [26, 0])}px)`,
          opacity: interpolate(pop, [0, 1], [0, 1]),
        }}
      >
        {page.words.map((w, i) => {
          const active = t >= w.s - 0.03 && t < (page.words[i + 1]?.s ?? page.end);
          const spoken = t >= w.s - 0.03;
          const wf = frame - Math.round(w.s * fps);
          const wp = spring({frame: wf, fps, config: {damping: 12, stiffness: 300, mass: 0.5}});
          const base = w.k === 2 ? 92 : 80;
          const color = active ? C.yellow : w.k === 2 ? C.yellow : w.k === 1 ? C.green : C.white;
          const scale = active ? interpolate(wp, [0, 1], [1, 1.12]) : 1;
          return (
            <span
              key={i}
              style={{
                fontFamily: MONT,
                fontWeight: 900,
                fontSize: base,
                lineHeight: 1.08,
                textTransform: 'uppercase',
                letterSpacing: -1,
                color,
                opacity: spoken ? 1 : 0.55,
                WebkitTextStroke: '14px #000',
                paintOrder: 'stroke fill',
                textShadow: active
                  ? `0 0 28px ${C.yellow}88, 0 8px 0 #000, 0 10px 24px rgba(0,0,0,.8)`
                  : '0 8px 0 #000, 0 10px 24px rgba(0,0,0,.8)',
                transform: `scale(${scale}) rotate(${active ? -2 : 0}deg)`,
                display: 'inline-block',
              }}
            >
              {w.w.replace(/[,.;:]$/, '')}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
