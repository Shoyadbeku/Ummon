import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {IslamicPattern, starPath} from './IslamicPattern';
import {LightRays, Particles} from './Overlays';

/** An ornate antique key, drawn at origin pointing right, ~360px long. */
const Key: React.FC<{id: string}> = ({id}) => (
  <g>
    <circle cx={0} cy={0} r={62} fill={`url(#kg${id})`} />
    <circle cx={0} cy={0} r={40} fill="#120b04" />
    <path d={starPath(30)} fill={`url(#kg${id})`} />
    <rect x={55} y={-11} width={260} height={22} rx={8} fill={`url(#kg${id})`} />
    <rect x={95} y={-17} width={16} height={34} rx={5} fill={`url(#kg${id})`} />
    <rect x={240} y={11} width={24} height={46} rx={3} fill={`url(#kg${id})`} />
    <rect x={272} y={11} width={18} height={30} rx={3} fill={`url(#kg${id})`} />
    <rect x={296} y={11} width={20} height={56} rx={3} fill={`url(#kg${id})`} />
    <rect x={60} y={-8} width={250} height={4} fill="#fff6da" opacity={0.6} />
  </g>
);

/**
 * "Its keys would burden a band of strong men" (Qasas 28:76) — keys rain down and pile up,
 * the pile grows heavier and the camera sinks under the weight.
 */
export const GoldenKeys: React.FC<{seed: string}> = ({seed}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const N = 18;
  const keys = useMemo(
    () =>
      new Array(N).fill(0).map((_, i) => ({
        x: 960 + (random(`${seed}k${i}`) - 0.5) * 1100,
        y: 640 + (random(`${seed}ky${i}`) - 0.3) * 260 - (i / N) * 120,
        rot: (random(`${seed}kr${i}`) - 0.5) * 300,
        sc: 0.55 + random(`${seed}ks${i}`) * 0.5,
        delay: Math.floor(i * 3.2 + random(`${seed}kd${i}`) * 4),
      })),
    [seed],
  );
  const glint = interpolate(frame, [20, 70], [-600, 1700], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const sink = interpolate(frame, [0, 110], [0, 25], {extrapolateRight: 'clamp'});
  const camS = interpolate(frame, [0, 120], [1.12, 1.0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 80% 60% at 50% 55%, #3a2408 0%, #140b03 55%, #040201 100%)'}}>
      <IslamicPattern opacity={0.12} reveal={40} />
      <LightRays intensity={0.9} />
      <AbsoluteFill style={{transform: `translateY(${sink}px) scale(${camS})`}}>
        <svg width="100%" height="100%" viewBox="0 0 1920 1080">
          <defs>
            {keys.map((_, i) => (
              <linearGradient key={i} id={`kg${seed}${i}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#fff0c2" />
                <stop offset="0.35" stopColor="#e9b84f" />
                <stop offset="0.7" stopColor="#a8701c" />
                <stop offset="1" stopColor="#5d3a0c" />
              </linearGradient>
            ))}
            <radialGradient id={`shadow${seed}`}>
              <stop offset="0" stopColor="#000" stopOpacity="0.7" />
              <stop offset="1" stopColor="#000" stopOpacity="0" />
            </radialGradient>
          </defs>
          <ellipse cx={960} cy={820} rx={760} ry={110} fill={`url(#shadow${seed})`} />
          {keys.map((k, i) => {
            const sp = spring({frame: frame - k.delay, fps, config: {damping: 11, mass: 0.9, stiffness: 140}});
            if (frame < k.delay) return null;
            const y = interpolate(sp, [0, 1], [-300, k.y]);
            const r = interpolate(sp, [0, 1], [k.rot - 90, k.rot]);
            return (
              <g key={i} transform={`translate(${k.x - 160 * k.sc},${y}) rotate(${r}) scale(${k.sc})`}>
                <Key id={`${seed}${i}`} />
              </g>
            );
          })}
        </svg>
        <AbsoluteFill
          style={{
            background: `linear-gradient(105deg, rgba(255,255,255,0) ${glint - 160}px, rgba(255,244,210,0.55) ${glint}px, rgba(255,255,255,0) ${glint + 160}px)`,
            mixBlendMode: 'overlay',
          }}
        />
      </AbsoluteFill>
      <Particles seed={`${seed}gp`} kind="gold" count={45} />
    </AbsoluteFill>
  );
};
