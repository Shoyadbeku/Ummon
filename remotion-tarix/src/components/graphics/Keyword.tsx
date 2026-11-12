import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

// Zarbali kalit so'z: kattadan tushadi, xromatik ajralish, fon qorayadi
export const Keyword: React.FC<{text: string; color?: string}> = ({text, color}) => {
  const frame = useCurrentFrame();
  const {durationInFrames: d} = useVideoConfig();
  const c = color ?? VIDEO.text;
  const s = interpolate(frame, [0, 8], [1.9, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const blur = interpolate(frame, [0, 8], [18, 0], clamp);
  const split = interpolate(frame, [6, 16], [14, 1.5], clamp);
  const drift = interpolate(frame, [8, d], [1, 1.06], clamp);
  const out = interpolate(frame, [d - 10, d], [1, 0], clamp);
  const dim = interpolate(frame, [0, 6, d - 10, d], [0, 0.55, 0.55, 0], clamp);
  const flash = interpolate(frame, [6, 8, 14], [0, 0.35, 0], clamp);
  const base: React.CSSProperties = {
    position: 'absolute', fontFamily: serif, fontWeight: 900, fontSize: 190, letterSpacing: 10, whiteSpace: 'nowrap',
  };
  return (
    <div style={{position: 'absolute', inset: 0}}>
      <div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${dim})`}} />
      <div style={{position: 'absolute', inset: 0, background: `rgba(255,240,210,${flash})`}} />
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: out, transform: `scale(${s * drift})`, filter: `blur(${blur}px)`}}>
        <div style={{position: 'relative'}}>
          <div style={{...base, position: 'relative', visibility: 'hidden'}}>{text}</div>
          <div style={{...base, left: -split, top: 0, color: 'rgba(255,40,40,0.55)', mixBlendMode: 'screen'}}>{text}</div>
          <div style={{...base, left: split, top: 0, color: 'rgba(40,160,255,0.55)', mixBlendMode: 'screen'}}>{text}</div>
          <div style={{...base, left: 0, top: 0, color: c, textShadow: `0 0 40px ${c}88, 0 10px 40px rgba(0,0,0,0.9)`}}>{text}</div>
        </div>
      </div>
    </div>
  );
};
