import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT} from '../fonts';
import {PAGES, Tone, FPS} from '../data/timing';
import {C, clamp} from './base';

const TONE: Record<Tone, string> = {gold: C.gold, green: C.green, red: C.red, accent: C.accent};
const ACTIVE = '#FFE14D';

/**
 * Hormozi-style word-by-word captions.
 * Centre line sits at y≈1270: above the Shorts/Reels/TikTok bottom UI (≈ last 380 px)
 * and clear of the right-hand action rail (words wrap inside 860 px).
 */
export const Captions: React.FC<{y?: number}> = ({y = 1270}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / FPS;

  const idx = PAGES.findIndex((p, i) => {
    const next = PAGES[i + 1];
    const end = next ? Math.min(next.s, p.e + 0.6) : p.e + 0.6;
    return t >= p.s - 0.03 && t < end;
  });
  if (idx < 0) return null;
  const page = PAGES[idx];
  const local = frame - Math.round(page.s * FPS);
  const pop = spring({frame: local, fps, config: {damping: 13, mass: 0.5, stiffness: 220}});

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 110,
          right: 110,
          top: y,
          transform: `translate(0, -50%) scale(${0.82 + 0.18 * pop}) translateY(${(1 - pop) * 26}px)`,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          columnGap: 0,
          rowGap: 4,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 84,
          lineHeight: 1.08,
          textTransform: 'uppercase',
          letterSpacing: -1,
        }}
      >
        {page.words.map((w, i) => {
          const wf = Math.round(w.s * FPS);
          const active = t >= w.s - 0.02 && t < w.e + 0.05;
          const said = t >= w.s - 0.02;
          const ws = spring({frame: frame - wf, fps, config: {damping: 10, mass: 0.4, stiffness: 260}});
          // Pop amount shrinks for long words so the scaled word never eats the inter-word gap.
          const amp = Math.min(0.14, 34 / (w.t.length * 52));
          const scale = active ? 1 + amp * ws - amp * 0.3 * interpolate(frame - wf, [6, 14], [0, 1], clamp) : 1;
          const color = w.tone ? TONE[w.tone] : active ? ACTIVE : C.white;
          const text = w.t.replace(/[,.]$/, '');
          return (
            <span key={i} style={{position: 'relative', display: 'inline-block', margin: '0 20px', transformOrigin: '50% 60%', transform: `scale(${scale}) rotate(${active ? -2 * ws + 2 : 0}deg)`, opacity: said ? 1 : 0.55}}>
              {/* outline layer */}
              <span
                aria-hidden
                style={{
                  position: 'absolute',
                  inset: 0,
                  WebkitTextStroke: '16px #000',
                  color: '#000',
                  filter: 'drop-shadow(0 8px 0 rgba(0,0,0,.55))',
                }}
              >
                {text}
              </span>
              <span style={{position: 'relative', color, textShadow: active && w.tone ? `0 0 28px ${color}` : undefined}}>{text}</span>
              {active && w.tone ? (
                <span
                  style={{
                    position: 'absolute',
                    left: -6,
                    right: -6,
                    bottom: -6,
                    height: 10,
                    borderRadius: 6,
                    background: color,
                    transformOrigin: 'left',
                    transform: `scaleX(${ws})`,
                  }}
                />
              ) : null}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
