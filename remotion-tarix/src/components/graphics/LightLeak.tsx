import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp} from './anim';

// Bob almashganda iliq yorug'lik "chaqnashi" (light leak / film burn)
export const LightLeak: React.FC<{seed?: number}> = ({seed = 0}) => {
  const frame = useCurrentFrame();
  const {durationInFrames: d} = useVideoConfig();
  const o = interpolate(frame, [0, d * 0.45, d], [0, 1, 0], clamp);
  const x = interpolate(frame, [0, d], [-20, 120], clamp) + (seed % 3) * 5;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: o, pointerEvents: 'none'}}>
      <AbsoluteFill style={{background: `radial-gradient(ellipse 60% 90% at ${x}% 40%, rgba(255,170,60,0.95), rgba(255,90,20,0.5) 35%, rgba(0,0,0,0) 70%)`}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse 40% 60% at ${100 - x}% 70%, rgba(255,220,160,0.6), rgba(0,0,0,0) 60%)`}} />
    </AbsoluteFill>
  );
};
