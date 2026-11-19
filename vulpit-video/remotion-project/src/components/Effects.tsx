import React from 'react';
import {AbsoluteFill, Img, interpolate, random, staticFile, useCurrentFrame} from 'remotion';
import {BAND_TOP, BAND_H, VOICE_LVL, SB, LAYOUT, pick} from '../data';

/** Static colour grade + depth gradients that tie all photographs together. */
export const Grade: React.FC = () => (
  <>
    {/* top & bottom atmosphere (keeps typography readable) */}
    {LAYOUT.landscape ? (
      <AbsoluteFill style={{background: 'linear-gradient(to bottom, rgba(3,6,8,0.62) 0px, rgba(3,6,8,0) 200px, rgba(3,6,8,0) 600px, rgba(3,6,8,0.55) 820px, rgba(3,6,8,0.9) 1080px)'}} />
    ) : <AbsoluteFill style={{background: `linear-gradient(to bottom, rgba(3,6,8,0.92) 0px, rgba(3,6,8,0.35) ${BAND_TOP + 60}px, rgba(3,6,8,0) ${BAND_TOP + 260}px, rgba(3,6,8,0) ${BAND_TOP + BAND_H - 420}px, rgba(3,6,8,0.55) ${BAND_TOP + BAND_H - 120}px, rgba(3,6,8,0.94) 1920px)`}} />}
    {/* teal/amber split tone */}
    <AbsoluteFill style={{background: 'linear-gradient(160deg, rgba(255,170,90,0.07), rgba(0,0,0,0) 45%, rgba(20,90,110,0.10))', mixBlendMode: 'soft-light'}} />
    {/* vignette */}
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 60% at 50% 46%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)'}} />
  </>
);

/** Animated film grain — 4 pre-rendered noise plates, offset deterministically each frame. */
export const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const i = f % 4;
  const ox = Math.floor(random(`gx${f}`) * 200) - 100;
  const oy = Math.floor(random(`gy${f}`) * 200) - 100;
  return (
    <AbsoluteFill style={{opacity: 0.075, mixBlendMode: 'overlay', overflow: 'hidden'}}>
      <Img src={staticFile(`fx/grain${i}.png`)} style={{position: 'absolute', left: -120 + ox, top: -120 + oy, width: 2160, height: 2160, imageRendering: 'pixelated'}} />
    </AbsoluteFill>
  );
};

/** Floating dust / spores catching light — brightness reacts to the narrator's voice. */
export const Particles: React.FC<{tint?: string}> = ({tint = '255,236,200'}) => {
  const f = useCurrentFrame();
  const lvl = VOICE_LVL[f] ?? 0;
  const items = new Array(34).fill(0).map((_, i) => {
    const sx = random(`px${i}`) * LAYOUT.W;
    const sy = random(`py${i}`) * LAYOUT.H;
    const sp = 0.15 + random(`ps${i}`) * 0.5;
    const size = 2 + random(`pz${i}`) * 5;
    const x = (sx + Math.sin((f + i * 40) / (60 + i * 3)) * 40 + f * sp * 0.4) % (LAYOUT.W + 40) - 20;
    const y = (sy - f * sp + LAYOUT.H * 4) % (LAYOUT.H + 60) - 30;
    const tw = 0.35 + 0.65 * Math.abs(Math.sin((f + i * 17) / (25 + i)));
    return {x, y, size, a: tw * (0.25 + 0.35 * lvl)};
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {items.map((p, i) => (
        <div key={i} style={{position: 'absolute', left: p.x, top: p.y, width: p.size, height: p.size, borderRadius: '50%', background: `rgba(${tint},${p.a})`, boxShadow: `0 0 ${p.size * 3}px rgba(${tint},${p.a * 0.8})`}} />
      ))}
    </AbsoluteFill>
  );
};

/** Warm light leak that sweeps across the frame for `dur` frames. */
export const LightLeak: React.FC<{dur: number; hue?: 'warm' | 'green'}> = ({dur, hue = 'warm'}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, dur * 0.3, dur], [0, 0.55, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const x = interpolate(f, [0, dur], [-20, 120]);
  const c = hue === 'warm' ? '255,150,60' : '90,255,160';
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: o, background: `radial-gradient(ellipse 60% 45% at ${x}% 30%, rgba(${c},0.9), rgba(${c},0) 70%), radial-gradient(ellipse 40% 30% at ${100 - x}% 80%, rgba(255,220,180,0.5), rgba(0,0,0,0) 70%)`}} />
  );
};

/** Thin story-progress line at the very top (retention device). */
export const Progress: React.FC = () => {
  const f = useCurrentFrame();
  const p = Math.max(0, (f - SB.hookFrames) / (SB.durationInFrames - SB.hookFrames));
  if (f < SB.hookFrames) return null;
  return (
    <div style={{position: 'absolute', left: pick(60, 90), right: pick(60, 90), top: pick(92, 30), height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.14)'}}>
      <div style={{width: `${p * 100}%`, height: '100%', borderRadius: 2, background: 'linear-gradient(90deg, #1FA968, #6CF0A0)', boxShadow: '0 0 12px rgba(108,240,160,0.7)'}} />
    </div>
  );
};

/** Fade from/to black at the very start and end. */
export const Bookends: React.FC = () => {
  const f = useCurrentFrame();
  const o = Math.max(
    interpolate(f, [0, 4], [1, 0], {extrapolateRight: 'clamp'}),
    interpolate(f, [SB.durationInFrames - 50, SB.durationInFrames - 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
  );
  return <AbsoluteFill style={{backgroundColor: '#000', opacity: o}} />;
};
