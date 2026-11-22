import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-50m.json';
import {ANTON, C, MONT, accent} from '../theme';

type Pin = {name: string; lon: number; lat: number; sub?: string};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries = (feature(world as any, (world as any).objects.countries) as any).features as any[];

export const MapScene: React.FC<{
  center: [number, number]; // lon, lat
  scaleFrom: number;
  scaleTo: number;
  highlight?: string[]; // country names
  pins: Pin[];
  color?: string;
  title?: string;
  arc?: boolean; // draw an arc between first two pins
}> = ({center, scaleFrom, scaleTo, highlight = [], pins, color, title, arc}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const z = interpolate(frame, [0, 70], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const scale = scaleFrom * Math.pow(scaleTo / scaleFrom, z);
  const projection = useMemo(() => geoMercator(), []);
  projection.center(center).scale(scale).translate([540, 820]);
  const path = geoPath(projection);

  const pts = pins.map((p) => projection([p.lon, p.lat]) as [number, number]);
  const arcPath = arc && pts.length > 1 ? (() => {
    const [a, b] = pts;
    const mx = (a[0] + b[0]) / 2;
    const my = Math.min(a[1], b[1]) - Math.abs(a[0] - b[0]) * 0.35 - 60;
    return `M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`;
  })() : null;
  const arcP = interpolate(frame, [40, 80], [0, 1], {...clamp, easing: Easing.inOut(Easing.quad)});

  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 42%, #10233a 0%, #060a12 70%)'}}>
      {/* grid */}
      <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px)', backgroundSize: '60px 60px'}} />
      <svg width={1080} height={1920} style={{position: 'absolute'}}>
        <defs>
          <filter id="glow"><feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {countries.map((f, i) => {
          const hl = highlight.includes(f.properties.name);
          return (
            <path
              key={i}
              d={path(f) ?? ''}
              fill={hl ? `${ac}33` : 'rgba(255,255,255,0.07)'}
              stroke={hl ? ac : 'rgba(255,255,255,0.25)'}
              strokeWidth={hl ? 3 : 1.2}
              filter={hl ? 'url(#glow)' : undefined}
            />
          );
        })}
        {arcPath && (
          <path d={arcPath} fill="none" stroke={ac} strokeWidth={6} strokeDasharray="2000" strokeDashoffset={2000 * (1 - arcP)} strokeLinecap="round" filter="url(#glow)" />
        )}
        {pts.map(([x, y], i) => {
          const s = spring({frame: frame - 30 - i * 14, fps, config: {damping: 10, stiffness: 200}});
          const ring = ((frame - 30 - i * 14) % 40) / 40;
          return (
            <g key={i} transform={`translate(${x},${y})`} opacity={s}>
              <circle r={14 + ring * 60} fill="none" stroke={ac} strokeWidth={4} opacity={(1 - ring) * 0.8} />
              <circle r={16 * s} fill={ac} stroke="#000" strokeWidth={4} />
            </g>
          );
        })}
      </svg>
      {pins.map((p, i) => {
        const [x, y] = pts[i];
        const s = spring({frame: frame - 38 - i * 14, fps, config: {damping: 14, stiffness: 170}});
        const left = x > 700;
        return (
          <div key={i} style={{position: 'absolute', left: left ? undefined : x + 34, right: left ? 1080 - x + 34 : undefined, top: y - 46, opacity: s, transform: `translateX(${interpolate(s, [0, 1], [left ? 40 : -40, 0])}px)`, textAlign: left ? 'right' : 'left'}}>
            <div style={{display: 'inline-block', background: '#000c', border: `3px solid ${ac}`, borderRadius: 12, padding: '8px 20px'}}>
              <div style={{fontFamily: ANTON, fontSize: 58, color: C.white, textTransform: 'uppercase', lineHeight: 1.05}}>{p.name}</div>
              {p.sub && <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 28, color: ac, textTransform: 'uppercase'}}>{p.sub}</div>}
            </div>
          </div>
        );
      })}
      {title && (
        <div style={{position: 'absolute', top: 210, left: 0, right: 0, textAlign: 'center', fontFamily: MONT, fontWeight: 900, fontSize: 46, letterSpacing: 10, color: ac, textTransform: 'uppercase', opacity: interpolate(frame, [0, 12], [0, 1], clamp)}}>
          {title}
        </div>
      )}
    </AbsoluteFill>
  );
};
