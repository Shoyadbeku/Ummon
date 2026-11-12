import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans, serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

// Xarita belgisi: pin tushadi, to'lqinlar tarqaladi, koordinatalar yozuv mashinkasida chiqadi
export const Location: React.FC<{place: string; country: string; coords: string}> = ({place, country, coords}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: d} = useVideoConfig();
  const drop = spring({frame, fps, config: {damping: 9, mass: 0.7}});
  const out = interpolate(frame, [d - 14, d], [1, 0], clamp);
  const ring = (frame % 40) / 40;
  const card = interpolate(frame, [8, 26], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const chars = Math.floor(interpolate(frame, [20, 20 + coords.length * 1.2], [0, coords.length], clamp));
  return (
    <div style={{position: 'absolute', right: 120, top: 130, opacity: out, display: 'flex', alignItems: 'center', gap: 26}}>
      <div style={{textAlign: 'right', opacity: card, transform: `translateX(${(1 - card) * 40}px)`}}>
        <div style={{fontFamily: sans, fontWeight: 600, fontSize: 20, letterSpacing: 8, color: VIDEO.accent}}>JOYLASHUV</div>
        <div style={{fontFamily: serif, fontWeight: 900, fontSize: 72, color: VIDEO.text, lineHeight: 1.05, textShadow: '0 4px 20px rgba(0,0,0,0.8)'}}>{place}</div>
        <div style={{fontFamily: sans, fontWeight: 500, fontSize: 26, color: VIDEO.text, opacity: 0.9, textShadow: '0 2px 8px #000'}}>{country}</div>
        <div style={{fontFamily: 'monospace', fontSize: 22, color: VIDEO.accent, marginTop: 8, letterSpacing: 2, textShadow: '0 2px 8px #000'}}>
          {coords.slice(0, chars)}
          <span style={{opacity: frame % 16 < 8 ? 1 : 0}}>▍</span>
        </div>
      </div>
      <div style={{position: 'relative', width: 90, height: 120}}>
        {[0, 0.5].map((k) => {
          const r = (ring + k) % 1;
          return (
            <div key={k} style={{position: 'absolute', left: 45 - 60 * r, top: 104 - 18 * r, width: 120 * r, height: 36 * r, borderRadius: '50%', border: `2px solid ${VIDEO.accent}`, opacity: (1 - r) * drop}} />
          );
        })}
        <svg width="90" height="120" viewBox="0 0 90 120" style={{position: 'absolute', left: 0, top: 0, transform: `translateY(${(1 - drop) * -140}px)`, filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.7))'}}>
          <path d="M45 115 C45 115 10 70 10 45 A35 35 0 1 1 80 45 C80 70 45 115 45 115 Z" fill={VIDEO.accent} />
          <circle cx="45" cy="45" r="14" fill="#120d06" />
        </svg>
      </div>
    </div>
  );
};
