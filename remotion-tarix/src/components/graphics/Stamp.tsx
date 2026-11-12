import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans} from '../../fonts';
import {clamp} from './anim';

const RED = '#c8322a';
// Rezina muhr: ekranga "uriladi"
export const Stamp: React.FC<{text: string; sub?: string}> = ({text, sub}) => {
  const frame = useCurrentFrame();
  const {durationInFrames: d} = useVideoConfig();
  const s = interpolate(frame, [0, 7], [2.6, 1], {...clamp, easing: Easing.in(Easing.quad)});
  const o = interpolate(frame, [0, 4], [0, 1], clamp) * interpolate(frame, [d - 12, d], [1, 0], clamp);
  const bounce = frame >= 7 && frame < 13 ? Math.sin((frame - 7) * 1.4) * 0.03 * (13 - frame) / 6 : 0;
  return (
    <div style={{position: 'absolute', right: 150, top: 170, opacity: o, transform: `rotate(-12deg) scale(${s + bounce})`}}>
      <div
        style={{
          border: `8px solid ${RED}`,
          outline: `3px solid ${RED}`,
          outlineOffset: 6,
          padding: '14px 40px 10px',
          textAlign: 'center',
          color: RED,
          fontFamily: sans,
          background: 'rgba(200,50,42,0.06)',
          mixBlendMode: 'screen',
          filter: 'url(#stamp-rough)',
        }}
      >
        <div style={{fontWeight: 700, fontSize: 96, letterSpacing: 10, lineHeight: 1}}>{text}</div>
        {sub ? <div style={{fontWeight: 700, fontSize: 24, letterSpacing: 8, marginTop: 8, borderTop: `3px solid ${RED}`, paddingTop: 8}}>{sub}</div> : null}
      </div>
      <svg width="0" height="0" style={{position: 'absolute'}}>
        <filter id="stamp-rough">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n" />
          <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.6" result="m" />
          <feComposite in="SourceGraphic" in2="m" operator="in" />
        </filter>
      </svg>
    </div>
  );
};
