import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C, clamp} from './base';
import {f, DURATION_S} from '../data/timing';

/** Animated film grain (SVG turbulence, reseeded every frame). */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.09}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity, mixBlendMode: 'overlay', pointerEvents: 'none'}}>
      <svg width="1080" height="1920">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 12} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: 'radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%)',
    }}
  />
);

/** Warm teal/orange split-tone, applied over everything as soft-light. */
export const SplitTone: React.FC = () => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      mixBlendMode: 'soft-light',
      background: 'linear-gradient(180deg, rgba(0,140,170,.35) 0%, rgba(0,0,0,0) 45%, rgba(255,140,40,.32) 100%)',
    }}
  />
);

/** Light leaks: drifting warm blooms at chosen moments (seconds). */
export const LightLeaks: React.FC<{at: number[]}> = ({at}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen'}}>
      {at.map((s, i) => {
        const lf = frame - f(s);
        if (lf < -2 || lf > 26) return null;
        const o = interpolate(lf, [0, 5, 26], [0, 0.85, 0], clamp);
        const x = interpolate(lf, [0, 26], [i % 2 ? 1150 : -150, i % 2 ? -100 : 1100]);
        const hue = i % 3 === 0 ? '255,120,40' : i % 3 === 1 ? '255,60,120' : '255,200,80';
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x - 600,
              top: 300 + (i % 4) * 280 - 600,
              width: 1200,
              height: 1200,
              borderRadius: '50%',
              opacity: o,
              background: `radial-gradient(circle, rgba(${hue},.9) 0%, rgba(${hue},.35) 35%, rgba(${hue},0) 70%)`,
              filter: 'blur(30px)',
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Hard exposure flash on beat cuts. */
export const Flashes: React.FC<{at: number[]}> = ({at}) => {
  const frame = useCurrentFrame();
  let o = 0;
  for (const s of at) {
    const lf = frame - f(s);
    if (lf >= 0 && lf < 6) o = Math.max(o, interpolate(lf, [0, 6], [0.7, 0], clamp));
  }
  if (o <= 0) return null;
  return <AbsoluteFill style={{background: '#fff', opacity: o, pointerEvents: 'none'}} />;
};

/** Thin retention progress bar at the very top. */
export const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const p = frame / f(DURATION_S);
  return (
    <div style={{position: 'absolute', top: 0, left: 0, height: 8, width: `${p * 100}%`, background: `linear-gradient(90deg, ${C.goldDeep}, ${C.gold})`, boxShadow: `0 0 18px ${C.gold}`}} />
  );
};
