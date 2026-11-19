import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONT_SANS, SUBS, SubPage, VOICE_LVL, pick} from '../data';

const findPage = (f: number): SubPage | null => {
  let lo = 0, hi = SUBS.length - 1, ans = -1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (SUBS[m].from <= f) { ans = m; lo = m + 1; } else hi = m - 1;
  }
  if (ans < 0) return null;
  const p = SUBS[ans];
  return f < p.to ? p : null;
};

/**
 * Word-synchronous kinetic subtitles. Words appear exactly when spoken (forced-alignment timestamps),
 * the active word pops and glows with the voice level, keywords keep their accent colour.
 */
export const Subtitles: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const page = findPage(f);
  if (!page) return null;
  const big = page.hook;
  const size = big ? pick(74, 66) : pick(60, 54);
  const out = interpolate(f, [page.to - 5, page.to], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const lvl = VOICE_LVL[f] ?? 0;
  return (
    <div
      style={{
        position: 'absolute', left: pick(50, 240), right: pick(50, 240), top: big ? pick(1390, 830) : pick(1470, 880), display: 'flex', flexWrap: 'wrap', justifyContent: 'center',
        alignItems: 'baseline', columnGap: size * 0.36, rowGap: 6, opacity: out, fontFamily: FONT_SANS, fontWeight: 800, fontSize: size,
        lineHeight: 1.18, letterSpacing: -0.5, textAlign: 'center',
      }}
    >
      {page.words.map((w, i) => {
        const shown = f >= w.s - 1;
        const active = f >= w.s - 1 && f < Math.max(w.e, w.s + 6);
        const sp = spring({frame: f - (w.s - 1), fps, config: {damping: 15, stiffness: 220, mass: 0.6}});
        const accent = w.k === 'g' ? COLORS.green : w.k === 'y' ? COLORS.gold : null;
        const color = active ? accent ?? '#FFE58A' : accent ?? COLORS.white;
        const scale = shown ? interpolate(sp, [0, 1], [0.6, 1]) * (active ? 1.05 : 1) : 0.6;
        const glow = active ? `0 0 ${18 + lvl * 26}px ${accent ? 'rgba(108,240,160,0.75)' : 'rgba(255,220,120,0.6)'}` : '0 0 0 transparent';
        return (
          <span
            key={i}
            style={{
              display: 'inline-block', color, transformOrigin: '50% 80%', opacity: shown ? Math.min(1, sp * 1.4) : 0, transform: `translateY(${shown ? (1 - sp) * 22 : 22}px) scale(${scale})`,
              textShadow: `0 4px 0 rgba(0,0,0,0.55), 0 0 14px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,1), ${glow}`,
              WebkitTextStroke: '1.5px rgba(0,0,0,0.55)',
            }}
          >
            {w.t}
          </span>
        );
      })}
    </div>
  );
};
