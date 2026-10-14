import React from 'react';
import {useCurrentFrame} from 'remotion';

/**
 * Prosedural bug' — yuqoriga ko'tariluvchi to'lqinsimon iplar.
 * `heat` = 1 → quyuq va baland bug', 0 → bug' yo'q.
 */
export const Steam: React.FC<{
  heat: number;
  width: number;
  height: number;
  wisps?: number;
  color?: string;
  style?: React.CSSProperties;
}> = ({heat, width, height, wisps = 6, color = '#FFFFFF', style}) => {
  const frame = useCurrentFrame();
  const cycle = 150;

  const paths = new Array(wisps).fill(0).map((_, i) => {
    const phase = (i / wisps) * cycle;
    const t = ((frame * (0.9 + (i % 3) * 0.15) + phase) % cycle) / cycle; // 0..1 hayot sikli
    const baseX = width * (0.18 + (0.64 * i) / Math.max(1, wisps - 1));
    const rise = t * height * 0.45;
    const len = height * (0.35 + heat * 0.45);
    const pts: string[] = [];
    const steps = 22;
    for (let s = 0; s <= steps; s++) {
      const p = s / steps;
      const y = height - rise - p * len;
      const amp = 10 + p * 38;
      const x = baseX + Math.sin(p * 5.5 + frame * 0.05 + i * 1.7) * amp + Math.sin(frame * 0.021 + i) * 12;
      pts.push(`${s === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`);
    }
    const life = Math.sin(t * Math.PI); // paydo bo'ladi -> yo'qoladi
    return {d: pts.join(' '), opacity: life * heat * 0.55, w: 16 + (i % 2) * 10};
  });

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow: 'visible', ...style}}>
      <defs>
        <filter id="steamBlur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="9" />
        </filter>
        <linearGradient id="steamFade" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={color} stopOpacity={0.2} />
          <stop offset="35%" stopColor={color} stopOpacity={1} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <g filter="url(#steamBlur)">
        {paths.map((p, i) => (
          <path
            key={i}
            d={p.d}
            stroke="url(#steamFade)"
            strokeWidth={p.w}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={p.opacity}
          />
        ))}
      </g>
    </svg>
  );
};
