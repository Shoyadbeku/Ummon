import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans, serif} from '../../fonts';
import {VIDEO} from '../../config';
import {clamp} from './anim';

type Side = {image: string; title: string; sub: string};

// Ikki tomonlama taqqoslash ekrani (diagonal bo'linish + VS)
export const Versus: React.FC<{left: Side; right: Side; rightAt: number}> = ({left, right, rightAt}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames: d} = useVideoConfig();
  const e = Easing.out(Easing.cubic);
  const lIn = interpolate(frame, [0, 16], [0, 1], {...clamp, easing: e});
  const rIn = interpolate(frame, [rightAt, rightAt + 16], [0, 1], {...clamp, easing: e});
  const vs = spring({frame: frame - rightAt - 8, fps, config: {damping: 10}});
  const out = interpolate(frame, [d - 16, d], [1, 0], clamp);
  const panel = (side: Side, isRight: boolean, k: number) => (
    <AbsoluteFill
      style={{
        clipPath: isRight ? 'polygon(56% 0, 100% 0, 100% 100%, 44% 100%)' : 'polygon(0 0, 56% 0, 44% 100%, 0 100%)',
        transform: `translateX(${(1 - k) * (isRight ? 900 : -900)}px)`,
        filter: isRight || rIn < 0.01 ? undefined : `brightness(${1 - 0.3 * rIn})`,
      }}
    >
      <Img src={staticFile(side.image)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${1.1 + frame * 0.0006})`, filter: 'sepia(0.2) contrast(1.05)'}} />
      <AbsoluteFill style={{background: isRight ? 'linear-gradient(to left, rgba(0,0,0,0.65), rgba(0,0,0,0) 45%)' : 'linear-gradient(to right, rgba(0,0,0,0.65), rgba(0,0,0,0) 45%)'}} />
      <div style={{position: 'absolute', top: 150, [isRight ? 'right' : 'left']: 110, textAlign: isRight ? 'right' : 'left', opacity: k}}>
        <div style={{fontFamily: serif, fontWeight: 900, fontSize: 80, color: VIDEO.text, textShadow: '0 4px 20px #000'}}>{side.title}</div>
        <div style={{display: 'inline-block', background: VIDEO.accent, color: '#120d06', fontFamily: sans, fontWeight: 700, fontSize: 28, letterSpacing: 4, padding: '8px 20px', marginTop: 10}}>{side.sub}</div>
      </div>
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill style={{opacity: out, backgroundColor: '#000'}}>
      {panel(left, false, lIn)}
      {panel(right, true, rIn)}
      <svg width="1920" height="1080" style={{position: 'absolute', inset: 0}}>
        <line x1={1920 * 0.56} y1={0} x2={1920 * 0.44} y2={1080} stroke={VIDEO.accent} strokeWidth="8" strokeDasharray="1200" strokeDashoffset={1200 * (1 - rIn)} style={{filter: `drop-shadow(0 0 14px ${VIDEO.accent})`}} />
      </svg>
      <div style={{position: 'absolute', left: 960 - 85, top: 540 - 85, width: 170, height: 170, borderRadius: '50%', background: '#120d06', border: `6px solid ${VIDEO.accent}`, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${vs}) rotate(${(1 - vs) * -90}deg)`, boxShadow: '0 0 40px rgba(217,164,65,0.6)'}}>
        <div style={{fontFamily: serif, fontWeight: 900, fontSize: 76, color: VIDEO.accent}}>VS</div>
      </div>
    </AbsoluteFill>
  );
};
