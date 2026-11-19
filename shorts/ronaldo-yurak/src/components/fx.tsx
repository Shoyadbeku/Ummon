import React, { createContext, useContext } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { noise2D } from '@remotion/noise';

export const C = {
  bg: '#07070a',
  red: '#ff2b3a',
  redDeep: '#a30d1a',
  gold: '#ffc94a',
  green: '#3dff8f',
  white: '#ffffff',
  cyan: '#4de8ff',
};

export const HEAD = 'Anton, Impact, sans-serif';
export const BODY = 'Montserrat, Arial, sans-serif';

/** Animated film grain (SVG turbulence, new seed every frame). */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.09 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: 'overlay', pointerEvents: 'none' }}>
      <svg width="100%" height="100%">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={frame % 97} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.75 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Warm drifting light leak, screen-blended. `at`/`dur` in frames, relative to parent. */
export const LightLeak: React.FC<{ at: number; dur: number; hue?: 'warm' | 'gold' | 'red'; intensity?: number }> = ({
  at,
  dur,
  hue = 'warm',
  intensity = 0.85,
}) => {
  const frame = useCurrentFrame() - at;
  if (frame < 0 || frame > dur) return null;
  const p = frame / dur;
  const o = interpolate(p, [0, 0.15, 0.6, 1], [0, intensity, intensity * 0.6, 0]);
  const x = interpolate(p, [0, 1], [-10, 110]);
  const cols = {
    warm: ['255,140,40', '255,60,20'],
    gold: ['255,210,90', '255,150,30'],
    red: ['255,40,60', '160,0,30'],
  }[hue];
  return (
    <AbsoluteFill
      style={{
        pointerEvents: 'none',
        mixBlendMode: 'screen',
        opacity: o,
        background: `radial-gradient(circle at ${x}% 30%, rgba(${cols[0]},0.9) 0%, rgba(${cols[0]},0) 38%),
                     radial-gradient(circle at ${100 - x * 0.7}% 80%, rgba(${cols[1]},0.7) 0%, rgba(${cols[1]},0) 45%)`,
      }}
    />
  );
};

/** Short white flash used on hard cuts. */
export const Flash: React.FC<{ at: number; dur?: number; max?: number; color?: string }> = ({
  at,
  dur = 6,
  max = 0.85,
  color = '#fff',
}) => {
  const frame = useCurrentFrame() - at;
  if (frame < 0 || frame > dur) return null;
  const o = interpolate(frame, [0, 1, dur], [max, max, 0], { extrapolateRight: 'clamp' });
  return <AbsoluteFill style={{ background: color, opacity: o, pointerEvents: 'none' }} />;
};

/** Camera shake offsets from smooth noise. */
export const shake = (frame: number, amount: number, seed = 'a') => ({
  x: noise2D(seed + 'x', frame * 0.35, 0) * amount,
  y: noise2D(seed + 'y', 0, frame * 0.35) * amount,
  r: noise2D(seed + 'r', frame * 0.2, 1) * amount * 0.04,
});

/** Glitch: RGB split + slice displacement over children for `dur` frames from `at`. */
export const Glitch: React.FC<{ at: number; dur?: number; children: React.ReactNode }> = ({ at, dur = 7, children }) => {
  const frame = useCurrentFrame();
  const local = frame - at;
  const active = local >= 0 && local < dur;
  const amt = active ? interpolate(local, [0, dur], [1, 0]) : 0;
  const dx = active ? noise2D('gx', frame, 0) * 40 * amt : 0;
  return (
    <AbsoluteFill style={{ transform: `translateX(${dx}px)`, filter: active ? 'url(#rgbsplit)' : undefined }}>
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <filter id="rgbsplit" x="-5%" y="-5%" width="110%" height="110%">
          <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
          <feOffset in="r" dx={18 * amt} dy="0" result="r2" />
          <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" result="gb" />
          <feOffset in="gb" dx={-18 * amt} dy="0" result="gb2" />
          <feBlend in="r2" in2="gb2" mode="screen" />
        </filter>
      </svg>
      {children}
      {active &&
        [0, 1, 2, 3].map((i) => {
          const y = ((noise2D('gy' + i, frame, 2) + 1) / 2) * 1800;
          const h = 20 + ((noise2D('gh' + i, frame, 3) + 1) / 2) * 90;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                top: y,
                height: h,
                background: i % 2 ? 'rgba(255,43,58,0.35)' : 'rgba(77,232,255,0.25)',
                mixBlendMode: 'screen',
                transform: `translateX(${noise2D('gs' + i, frame, 4) * 120}px)`,
              }}
            />
          );
        })}
    </AbsoluteFill>
  );
};

/** Beat pulse: returns 0..1 envelope that spikes on each beat time (seconds). */
export const beatPulse = (frame: number, fps: number, beats: number[], decay = 6) => {
  const t = frame / fps;
  let v = 0;
  for (const b of beats) {
    const d = t - b;
    if (d >= 0 && d < 0.6) v = Math.max(v, Math.exp(-d * decay));
  }
  return v;
};

export const useSec = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps;
};

/** Absolute (composition) frame offset of the enclosing scene. */
export const SceneStart = createContext(0);
export const useAbsFrame = () => useCurrentFrame() + useContext(SceneStart);
