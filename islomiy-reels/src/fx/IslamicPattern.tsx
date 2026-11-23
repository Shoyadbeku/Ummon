import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

/** Eight-point star (Rub el Hizb) path centred at 0,0 with outer radius r. */
export const starPath = (r: number) => {
  const pts: string[] = [];
  for (let i = 0; i < 16; i++) {
    const a = (Math.PI / 8) * i - Math.PI / 2;
    const rr = i % 2 === 0 ? r : r * 0.72;
    pts.push(`${(Math.cos(a) * rr).toFixed(2)},${(Math.sin(a) * rr).toFixed(2)}`);
  }
  return `M${pts.join('L')}Z`;
};

/** Animated gold geometric lattice, revealed radially, slowly rotating. */
export const IslamicPattern: React.FC<{opacity?: number; reveal?: number}> = ({opacity = 0.16, reveal = 30}) => {
  const frame = useCurrentFrame();
  const rot = frame * 0.04;
  const rad = interpolate(frame, [0, reveal], [0, 75], {extrapolateRight: 'clamp'});
  const T = 180;
  return (
    <AbsoluteFill
      style={{
        opacity,
        mixBlendMode: 'screen',
        maskImage: `radial-gradient(circle at 50% 45%, black ${rad * 0.6}%, transparent ${rad}%)`,
        WebkitMaskImage: `radial-gradient(circle at 50% 45%, black ${rad * 0.6}%, transparent ${rad}%)`,
      }}
    >
      <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{transform: `rotate(${rot}deg) scale(1.5)`}}>
        <defs>
          <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#fff1c9" />
            <stop offset="0.5" stopColor="#d9a441" />
            <stop offset="1" stopColor="#8a5a17" />
          </linearGradient>
          <pattern id="lattice" width={T} height={T} patternUnits="userSpaceOnUse">
            <g transform={`translate(${T / 2},${T / 2})`} fill="none" stroke="url(#pg)" strokeWidth="2">
              <path d={starPath(T * 0.42)} />
              <path d={starPath(T * 0.24)} />
              <rect x={-T * 0.3} y={-T * 0.3} width={T * 0.6} height={T * 0.6} transform="rotate(45)" />
              <line x1={-T / 2} y1={0} x2={-T * 0.42} y2={0} />
              <line x1={T * 0.42} y1={0} x2={T / 2} y2={0} />
              <line x1={0} y1={-T / 2} x2={0} y2={-T * 0.42} />
              <line x1={0} y1={T * 0.42} x2={0} y2={T / 2} />
            </g>
          </pattern>
        </defs>
        <rect x={-1920} y={-1080} width={5760} height={3240} fill="url(#lattice)" />
      </svg>
    </AbsoluteFill>
  );
};

/** Ornamental frame used around verse references. */
export const StarOrnament: React.FC<{size: number; color?: string}> = ({size, color = '#e6b85c'}) => (
  <svg width={size} height={size} viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`}>
    <path d={starPath(size * 0.48)} fill="none" stroke={color} strokeWidth={2} />
    <path d={starPath(size * 0.3)} fill={color} opacity={0.85} />
  </svg>
);
