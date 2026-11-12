import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans, serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

// Katta raqam sanab chiqadi + aylana progress
export const Stat: React.FC<{value: number; suffix?: string; label: string; sub?: string}> = ({value, suffix, label, sub}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: d} = useVideoConfig();
  const p = interpolate(frame, [0, fps * 1.4], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const out = interpolate(frame, [d - 14, d], [1, 0], clamp);
  const ent = interpolate(frame, [0, 14], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.6))});
  const R = 150;
  const C = 2 * Math.PI * R;
  return (
    <div style={{position: 'absolute', right: 140, top: 170, width: 360, height: 360, opacity: out * Math.min(1, ent + 0.2), transform: `scale(${0.7 + 0.3 * ent})`}}>
      <svg width="360" height="360" style={{position: 'absolute', inset: 0}}>
        <circle cx="180" cy="180" r={R + 18} fill="rgba(8,6,4,0.62)" />
        <circle cx="180" cy="180" r={R} stroke="rgba(244,234,214,0.15)" strokeWidth="4" fill="none" />
        <circle cx="180" cy="180" r={R} stroke={VIDEO.accent} strokeWidth="6" fill="none" strokeDasharray={C} strokeDashoffset={C * (1 - p)} strokeLinecap="round" transform="rotate(-90 180 180)" style={{filter: `drop-shadow(0 0 8px ${VIDEO.accent})`}} />
      </svg>
      <div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
        <div style={{fontFamily: serif, fontWeight: 900, fontSize: value >= 1000 ? 96 : 120, color: VIDEO.text, lineHeight: 1}}>
          {Math.round(value * p)}
          {suffix ?? ''}
        </div>
        <div style={{fontFamily: sans, fontWeight: 700, fontSize: 26, letterSpacing: 10, color: VIDEO.accent, marginTop: 6}}>{label}</div>
        {sub ? <div style={{fontFamily: sans, fontWeight: 500, fontSize: 17, color: VIDEO.text, opacity: 0.85 * p, marginTop: 10, maxWidth: 240}}>{sub}</div> : null}
      </div>
    </div>
  );
};
