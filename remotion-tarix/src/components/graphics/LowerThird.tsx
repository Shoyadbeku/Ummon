import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans, serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

export const LowerThird: React.FC<{name: string; role: string}> = ({name, role}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: d} = useVideoConfig();
  const e = Easing.out(Easing.cubic);
  const bar = interpolate(frame, [0, 12], [0, 1], {...clamp, easing: e});
  const reveal = interpolate(frame, [6, 24], [0, 100], {...clamp, easing: e});
  const role2 = interpolate(frame, [16, 32], [0, 100], {...clamp, easing: e});
  const out = interpolate(frame, [d - 14, d], [1, 0], clamp);
  const outX = interpolate(frame, [d - 14, d], [0, -60], {...clamp, easing: Easing.in(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: 110, bottom: 250, opacity: out, transform: `translateX(${outX}px)`, display: 'flex', alignItems: 'stretch', gap: 22}}>
      <div style={{width: 6, background: VIDEO.accent, transform: `scaleY(${bar})`, transformOrigin: 'bottom', boxShadow: `0 0 18px ${VIDEO.accent}`}} />
      <div>
        <div style={{clipPath: `inset(0 ${100 - reveal}% 0 0)`, background: 'rgba(10,8,6,0.78)', padding: '10px 26px 8px', backdropFilter: 'blur(6px)'}}>
          <div style={{fontFamily: serif, fontWeight: 700, fontSize: 58, color: VIDEO.text, lineHeight: 1.1}}>{name}</div>
        </div>
        <div style={{clipPath: `inset(0 ${100 - role2}% 0 0)`, background: VIDEO.accent, padding: '8px 26px', display: 'inline-block'}}>
          <div style={{fontFamily: sans, fontWeight: 700, fontSize: 24, letterSpacing: 4, color: '#120d06', textTransform: 'uppercase'}}>{role}</div>
        </div>
      </div>
      <div style={{position: 'absolute', left: 28, top: -16, fontFamily: sans, fontSize: 14, letterSpacing: 6, color: VIDEO.accent, opacity: role2 / 100}}>
        ● ARXIV
      </div>
    </div>
  );
};
