import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans, serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

// Yakuniy savol kartasi — tomoshabinni izoh yozishga chorlaydi
export const Question: React.FC<{title: string; a: string; b: string; cta: string}> = ({title, a, b, cta}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: d} = useVideoConfig();
  const bg = interpolate(frame, [0, 15], [0, 0.6], clamp);
  const t = spring({frame, fps, config: {damping: 200}});
  const ca = spring({frame: frame - 12, fps, config: {damping: 14}});
  const cb = spring({frame: frame - Math.min(d * 0.45, 140), fps, config: {damping: 14}});
  const cta2 = spring({frame: frame - Math.min(d * 0.7, 230), fps, config: {damping: 12}});
  const out = interpolate(frame, [d - 10, d], [1, 0], clamp);
  const card = (label: string, letter: string, k: number) => (
    <div style={{display: 'flex', alignItems: 'center', gap: 22, background: 'rgba(12,9,6,0.85)', border: `2px solid ${VIDEO.accent}`, padding: '22px 34px', width: 620, transform: `translateY(${(1 - k) * 40}px) scale(${0.9 + 0.1 * k})`, opacity: k}}>
      <div style={{width: 64, height: 64, borderRadius: '50%', background: VIDEO.accent, color: '#120d06', fontFamily: serif, fontWeight: 900, fontSize: 38, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{letter}</div>
      <div style={{fontFamily: sans, fontWeight: 600, fontSize: 36, color: VIDEO.text}}>{label}</div>
    </div>
  );
  return (
    <div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${bg})`, opacity: out, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 30, paddingBottom: 120}}>
      <div style={{fontFamily: sans, fontWeight: 600, fontSize: 24, letterSpacing: 10, color: VIDEO.accent, opacity: t}}>SIZNINGCHA</div>
      <div style={{fontFamily: serif, fontWeight: 900, fontSize: 76, color: VIDEO.text, opacity: t, transform: `translateY(${(1 - t) * 20}px)`, textShadow: '0 4px 20px #000'}}>{title}?</div>
      <div style={{display: 'flex', gap: 40, marginTop: 10}}>
        {card(a, 'A', ca)}
        {card(b, 'B', cb)}
      </div>
      <div style={{fontFamily: sans, fontWeight: 700, fontSize: 30, color: '#fff', background: '#c4302b', padding: '14px 36px', borderRadius: 8, marginTop: 16, transform: `scale(${cta2})`}}>💬 {cta}</div>
    </div>
  );
};
