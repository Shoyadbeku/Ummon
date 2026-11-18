import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {PAGES} from './data/words';
import {GREEN, MONT, YELLOW} from './fx';

// Hormozi-style word-by-word captions, placed in the lower safe zone
// (above TikTok/Reels/Shorts bottom UI, clear of the right-side action rail).
export const Captions: React.FC<{y?: number}> = ({y = 1300}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const page = PAGES.find((p) => t >= p.s && t < p.e + 0.05);
  if (!page) return null;
  const pf = Math.round(page.s * fps);
  const enter = spring({frame: frame - pf, fps, config: {damping: 14, stiffness: 220, mass: 0.6}});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', paddingLeft: 90, paddingRight: 130}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '4px 34px', maxWidth: 880,
        transform: `translateY(${(1 - enter) * 30}px) scale(${0.75 + 0.25 * enter})`, opacity: Math.min(1, enter * 2)}}>
        {page.words.map((w, i) => {
          const active = t >= w.s && t < (page.words[i + 1]?.s ?? page.e + 0.05);
          const spoken = t >= w.s;
          const wf = Math.round(w.s * fps);
          const pop = spring({frame: frame - wf, fps, config: {damping: 10, stiffness: 320, mass: 0.5}});
          const color = active ? (w.kw ? GREEN : YELLOW) : spoken ? 'white' : 'rgba(255,255,255,0.85)';
          const sc = active ? interpolate(pop, [0, 1], [0.92, w.kw ? 1.1 : 1.06]) : 1;
          return (
            <span key={i} style={{
              fontFamily: MONT, fontWeight: 900, fontSize: w.kw ? 88 : 82, lineHeight: 1.12, textTransform: 'uppercase',
              color, WebkitTextStroke: '14px black', paintOrder: 'stroke fill', letterSpacing: -1,
              display: 'inline-block', transform: `scale(${sc}) rotate(${active ? -2 : 0}deg)`,
              textShadow: '0 8px 0 rgba(0,0,0,0.65), 0 0 30px rgba(0,0,0,0.5)',
            }}>{w.w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
