import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, random, useCurrentFrame} from 'remotion';

type Seg = {x1: number; y1: number; x2: number; y2: number; w: number; t: number};

/**
 * Jagged ground-fissure generator (deterministic per seed).
 * Each crack is a chain of short straight segments whose width tapers from the epicentre,
 * revealed segment by segment so the fracture "races" outwards.
 */
const makeCracks = (seed: string, cy: number): Seg[] => {
  const segs: Seg[] = [];
  const walk = (x: number, y: number, ang: number, steps: number, w: number, t0: number, depth: number, id: string) => {
    for (let i = 0; i < steps; i++) {
      ang += (random(`${seed}${id}a${i}`) - 0.5) * 1.1;
      // keep the fracture travelling roughly horizontally across the ground plane
      ang = ang * 0.85 + (Math.cos(ang) > 0 ? 0 : Math.PI) * 0.15;
      const st = 26 + random(`${seed}${id}s${i}`) * 34;
      const nx = x + Math.cos(ang) * st;
      const ny = y + Math.sin(ang) * st * 0.38;
      const k = i / steps;
      segs.push({x1: x, y1: y, x2: nx, y2: ny, w: Math.max(2, w * (1 - k * 0.85)), t: t0 + i * 1.05});
      x = nx;
      y = ny;
      if (depth < 1 && i > 3 && random(`${seed}${id}b${i}`) > 0.86) {
        const d = random(`${seed}${id}bd${i}`) > 0.5 ? 1 : -1;
        walk(x, y, ang + d * (0.7 + random(`${seed}${id}ba${i}`) * 0.6), Math.floor((steps - i) * 0.5), w * (1 - k) * 0.6, t0 + i * 1.05, depth + 1, `${id}-${i}`);
      }
    }
  };
  walk(960, cy, Math.PI + 0.05, 34, 34, 0, 0, 'L');
  walk(960, cy, -0.05, 34, 34, 0, 0, 'R');
  walk(960, cy, Math.PI * 0.62, 8, 18, 6, 1, 'D');
  walk(960, cy, -Math.PI * 0.4, 7, 16, 8, 1, 'U');
  return segs;
};

/** Ground splitting open: tapered dark fissures with sun-lit rims and a widening pit of darkness. */
export const EarthCracks: React.FC<{seed: string; cy?: number}> = ({seed, cy = 760}) => {
  const frame = useCurrentFrame();
  const segs = useMemo(() => makeCracks(seed, cy), [seed, cy]);
  const pit = interpolate(frame, [18, 105], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad)});
  const dark = interpolate(frame, [0, 120], [0, 0.42], {extrapolateRight: 'clamp'});
  const widen = 1 + pit * 1.4;
  const visible = segs.filter((s) => frame >= s.t);
  const grow = (s: Seg) => interpolate(frame, [s.t, s.t + 2.5], [0, 1], {extrapolateRight: 'clamp'});
  const pt = (s: Seg) => {
    const g = grow(s);
    return {x2: s.x1 + (s.x2 - s.x1) * g, y2: s.y1 + (s.y2 - s.y1) * g};
  };
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: `rgba(0,0,0,${dark})`}} />
      <svg width="100%" height="100%" viewBox="0 0 1920 1080">
        <defs>
          <radialGradient id={`pit${seed}`} cx="50%" cy="50%" r="50%">
            <stop offset="0" stopColor="#000" stopOpacity="1" />
            <stop offset="0.55" stopColor="#030100" stopOpacity="0.92" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
          <filter id={`sh${seed}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="7" />
          </filter>
        </defs>
        {/* soft shadow around the fissures (depth) */}
        <g filter={`url(#sh${seed})`} opacity={0.75}>
          {visible.map((s, i) => {
            const p = pt(s);
            return <line key={`s${i}`} x1={s.x1} y1={s.y1} x2={p.x2} y2={p.y2} stroke="#1a0d04" strokeWidth={s.w * widen * 2.2} strokeLinecap="round" />;
          })}
        </g>
        {/* lit upper rim */}
        {visible.map((s, i) => {
          const p = pt(s);
          return <line key={`r${i}`} x1={s.x1} y1={s.y1 - s.w * 0.45} x2={p.x2} y2={p.y2 - s.w * 0.45} stroke="#f3d6a2" strokeOpacity={0.55} strokeWidth={Math.max(1.5, s.w * 0.35)} strokeLinecap="round" />;
        })}
        {/* the void */}
        {visible.map((s, i) => {
          const p = pt(s);
          return <line key={`v${i}`} x1={s.x1} y1={s.y1} x2={p.x2} y2={p.y2} stroke="#050201" strokeWidth={s.w * widen} strokeLinecap="round" />;
        })}
        <ellipse cx={960} cy={cy + 6} rx={560 * pit} ry={130 * pit} fill={`url(#pit${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};
