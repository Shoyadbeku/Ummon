import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

/* ---------- Global finishing layers ---------- */

export const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse 85% 70% at 50% 46%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.38) 78%, rgba(0,0,0,0.82) 100%)',
      pointerEvents: 'none',
    }}
  />
);

/** Unifying "film look": crushed deep blacks + warm gold highlights + emerald shadow tint. */
export const FilmLook: React.FC = () => (
  <>
    <AbsoluteFill style={{background: 'rgba(6, 34, 26, 0.16)', mixBlendMode: 'soft-light'}} />
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, rgba(255,196,110,0.10) 0%, rgba(0,0,0,0) 40%, rgba(0,0,0,0) 70%, rgba(0,0,0,0.35) 100%)',
        mixBlendMode: 'overlay',
      }}
    />
  </>
);

export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.08}) => {
  const frame = useCurrentFrame();
  const x = Math.floor(random(`gx${frame}`) * 256);
  const y = Math.floor(random(`gy${frame}`) * 256);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url(${staticFile('images/grain.png')})`,
        backgroundPosition: `${x}px ${y}px`,
        backgroundSize: '256px 256px',
        opacity,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }}
    />
  );
};

/* ---------- Per-shot atmosphere layers ---------- */

/** Volumetric light rays falling from the top of the frame. */
export const LightRays: React.FC<{intensity?: number; warm?: boolean}> = ({intensity = 1, warm = true}) => {
  const frame = useCurrentFrame();
  const rot = Math.sin(frame / 90) * 4;
  const breathe = 0.75 + 0.25 * Math.sin(frame / 37);
  const c = warm ? '255,214,140' : '200,255,230';
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: 0.38 * intensity * breathe, pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: '-40%',
          top: '-30%',
          width: '180%',
          height: '120%',
          transformOrigin: '50% 0%',
          transform: `rotate(${rot}deg)`,
          background: `repeating-conic-gradient(from 160deg at 50% 0%, rgba(${c},0.0) 0deg, rgba(${c},0.32) 2.2deg, rgba(${c},0.0) 5deg, rgba(${c},0.0) 9deg)`,
          maskImage: 'linear-gradient(180deg, black 0%, rgba(0,0,0,0.6) 45%, transparent 85%)',
          WebkitMaskImage: 'linear-gradient(180deg, black 0%, rgba(0,0,0,0.6) 45%, transparent 85%)',
          filter: 'blur(6px)',
        }}
      />
      <AbsoluteFill
        style={{background: `radial-gradient(ellipse 60% 35% at 50% 0%, rgba(${c},0.55), rgba(${c},0) 70%)`}}
      />
    </AbsoluteFill>
  );
};

/** Floating particles: golden bokeh or desert dust. Deterministic (seeded). */
export const Particles: React.FC<{seed: string; count?: number; kind: 'gold' | 'dust'}> = ({seed, count = 40, kind}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const parts = useMemo(
    () =>
      new Array(count).fill(0).map((_, i) => ({
        x: random(`${seed}px${i}`) * width,
        y: random(`${seed}py${i}`) * height,
        r: (kind === 'gold' ? 3 : 1.5) + random(`${seed}pr${i}`) * (kind === 'gold' ? 16 : 5),
        v: 0.4 + random(`${seed}pv${i}`) * 1.6,
        ph: random(`${seed}pp${i}`) * Math.PI * 2,
        depth: random(`${seed}pd${i}`),
      })),
    [seed, count, kind, width, height],
  );
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', pointerEvents: 'none'}}>
      {parts.map((p, i) => {
        const yy = (p.y - frame * p.v * (kind === 'gold' ? 1.4 : 0.6) + height * 4) % (height + 80) - 40;
        const xx = p.x + Math.sin(frame / 40 + p.ph) * 26 + (kind === 'dust' ? frame * p.v * 0.9 : 0);
        const tw = 0.45 + 0.55 * Math.abs(Math.sin(frame / 22 + p.ph));
        const col = kind === 'gold' ? '255,205,120' : '255,230,190';
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: ((xx % width) + width) % width,
              top: yy,
              width: p.r * 2,
              height: p.r * 2,
              borderRadius: '50%',
              background: `radial-gradient(circle, rgba(${col},${0.85 * tw}) 0%, rgba(${col},0) 70%)`,
              opacity: kind === 'gold' ? 0.55 + p.depth * 0.45 : 0.35 + p.depth * 0.4,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Soft breathing glow (used on manuscripts and sacred places). */
export const Glow: React.FC = () => {
  const frame = useCurrentFrame();
  const o = 0.22 + 0.1 * Math.sin(frame / 28);
  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse 55% 40% at 50% 45%, rgba(255,200,120,0.9), rgba(255,200,120,0) 70%)',
        mixBlendMode: 'soft-light',
        opacity: o,
      }}
    />
  );
};

/** Golden flash / light-leak used for "flash" transitions. */
export const LightFlash: React.FC<{frame: number}> = ({frame}) => {
  const o = interpolate(frame, [0, 2, 14], [0, 0.95, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (o <= 0) return null;
  return (
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(ellipse 80% 60% at 50% 45%, rgba(255,246,225,1) 0%, rgba(255,196,110,0.85) 35%, rgba(255,150,60,0) 75%)',
        mixBlendMode: 'screen',
        opacity: o,
      }}
    />
  );
};

/** Lightning: double flash at the start of the shot plus a late one. */
export const Lightning: React.FC<{seed: string}> = ({seed}) => {
  const frame = useCurrentFrame();
  const late = 40 + Math.floor(random(seed) * 40);
  const f = (c: number) => interpolate(frame, [c - 1, c, c + 5], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o = Math.max(f(9), f(14) * 0.7, f(late) * 0.6);
  if (o <= 0.01) return null;
  return <AbsoluteFill style={{background: 'rgba(220,235,255,1)', mixBlendMode: 'overlay', opacity: o}} />;
};

export const Img2: typeof Img = Img;
