import React from 'react';
import {AbsoluteFill, staticFile, useCurrentFrame, interpolate} from 'remotion';

// Animated film grain from 6 pre-rendered noise tiles
export const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const i = f % 6;
  const ox = (f * 137) % 512, oy = (f * 251) % 512;
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `url(${staticFile(`fx/grain${i}.png`)})`, backgroundSize: '512px 512px',
        backgroundPosition: `${ox}px ${oy}px`, mixBlendMode: 'overlay', opacity: 0.16, pointerEvents: 'none',
      }}
    />
  );
};

export const Flash: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 3, 10], [0, 0.85, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#fff', opacity: o, mixBlendMode: 'screen'}} />;
};

export const LightLeak: React.FC = () => {
  const f = useCurrentFrame();
  const x = interpolate(f, [0, 40], [-30, 130]);
  const o = interpolate(f, [0, 8, 28, 40], [0, 0.7, 0.4, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${x}% 30%, rgba(255,150,40,0.9) 0%, rgba(255,60,20,0.5) 18%, rgba(255,0,80,0) 45%)`,
        mixBlendMode: 'screen', opacity: o,
      }}
    />
  );
};
