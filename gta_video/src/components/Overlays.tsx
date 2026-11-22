import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame} from 'remotion';

// Film grain: 4 pre-rendered noise tiles cycled every 2 frames
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.09}) => {
  const frame = useCurrentFrame();
  const idx = Math.floor(frame / 2) % 4;
  return (
    <AbsoluteFill style={{mixBlendMode: 'overlay', opacity, pointerEvents: 'none'}}>
      <Img src={staticFile(`fx/grain${idx}.png`)} style={{width: '100%', height: '100%', imageRendering: 'auto'}} />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{strength?: number}> = ({strength = 0.75}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse 80% 70% at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,${strength}) 100%)`,
      pointerEvents: 'none',
    }}
  />
);

// Soft top/bottom gradients so captions and titles always read
export const SafeGradients: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 52%, rgba(0,0,0,.72) 78%, rgba(0,0,0,.85) 100%)',
      pointerEvents: 'none',
    }}
  />
);

// Light leak sweeping across the frame at a cut. `at` = frame of the cut.
export const LightLeak: React.FC<{at: number; seed: number; dur?: number}> = ({at, seed, dur = 22}) => {
  const frame = useCurrentFrame();
  const f = frame - at;
  if (f < -4 || f > dur) return null;
  const p = interpolate(f, [-4, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const op = interpolate(f, [-4, 2, dur], [0, 0.85, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const hue = [28, 340, 45, 15][Math.floor(random(seed) * 4)];
  const x = interpolate(p, [0, 1], [-30, 130]);
  const y = 20 + random(seed + 1) * 60;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: op, pointerEvents: 'none'}}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 55% 40% at ${x}% ${y}%, hsla(${hue},100%,62%,.9) 0%, hsla(${hue + 20},100%,50%,.35) 40%, rgba(0,0,0,0) 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 35% 60% at ${100 - x}% ${100 - y}%, hsla(${hue - 25},100%,60%,.55) 0%, rgba(0,0,0,0) 65%)`,
        }}
      />
    </AbsoluteFill>
  );
};

// Quick white/colored flash at a cut
export const Flash: React.FC<{at: number; color?: string; dur?: number}> = ({at, color = '#fff', dur = 6}) => {
  const frame = useCurrentFrame();
  const f = frame - at;
  if (f < 0 || f > dur) return null;
  const op = interpolate(f, [0, dur], [0.75, 0]);
  return <AbsoluteFill style={{background: color, opacity: op, pointerEvents: 'none'}} />;
};

// Letterbox bars, used sparingly for "cinematic" chapters
export const Letterbox: React.FC<{size?: number}> = ({size = 120}) => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: size, background: '#000'}} />
    <div style={{position: 'absolute', bottom: 0, left: 0, right: 0, height: size, background: '#000'}} />
  </AbsoluteFill>
);
