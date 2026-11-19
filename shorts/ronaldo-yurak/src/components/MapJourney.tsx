import React, { useMemo } from 'react';
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { geoMercator, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';
import { evolvePath, getLength } from '@remotion/paths';
import world from 'world-atlas/countries-50m.json';
import { BODY, C, HEAD } from './fx';

type Stop = { name: string; sub: string; lonlat: [number, number]; at: number; img: string; country: string };

const W = 1080;
const H = 1920;

/**
 * Animated career map: Manchester → Madrid → Lisbon (Portugal NT).
 * Camera follows the travelling head; the active country lights up and a
 * photo card flips in on arrival. `at` values are local frames.
 */
export const MapJourney: React.FC<{ stops: Stop[]; dur: number }> = ({ stops, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const { countries, projection, path } = useMemo(() => {
    const topo = world as any;
    const fc = feature(topo, topo.objects.countries) as any;
    const proj = geoMercator().fitExtent(
      [
        [60, 200],
        [W - 60, H - 300],
      ],
      { type: 'MultiPoint', coordinates: [[-11, 35.5], [5, 35.5], [-11, 57], [5, 57]] } as any,
    );
    return { countries: fc.features as any[], projection: proj, path: geoPath(proj) };
  }, []);

  const pts = stops.map((s) => projection(s.lonlat) as [number, number]);
  // one smooth curve per leg
  const legs = pts.slice(1).map((p, i) => {
    const a = pts[i];
    const mx = (a[0] + p[0]) / 2 + (i === 0 ? 260 : -120);
    const my = (a[1] + p[1]) / 2;
    return `M ${a[0]} ${a[1]} Q ${mx} ${my} ${p[0]} ${p[1]}`;
  });

  // camera target: the stop being travelled to
  let cam = pts[0];
  let active = 0;
  for (let i = 0; i < stops.length; i++) if (frame >= stops[i].at - 10) active = i;
  if (active > 0) {
    const legStart = stops[active].at - 22;
    const k = interpolate(frame, [legStart, stops[active].at], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.inOut(Easing.cubic),
    });
    cam = [pts[active - 1][0] + (pts[active][0] - pts[active - 1][0]) * k, pts[active - 1][1] + (pts[active][1] - pts[active - 1][1]) * k];
  }
  const intro = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const zoom = interpolate(intro, [0, 1], [1.0, 1.55]) + interpolate(frame, [0, dur], [0, 0.12]);
  const tx = W / 2 - cam[0] * zoom;
  const ty = H * 0.42 - cam[1] * zoom;
  const camT = `translate(${tx * intro + (1 - intro) * 0}px, ${ty * intro}px) scale(${zoom})`;

  const lit = stops.filter((s) => frame >= s.at).map((s) => s.country);
  const activeCountry = stops[active].country;

  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 40%, #0d1b2a 0%, #04070c 70%)' }}>
      {/* grid */}
      <AbsoluteFill
        style={{
          opacity: 0.25,
          backgroundImage:
            'linear-gradient(rgba(77,232,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(77,232,255,0.15) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          transform: `translate(${(-frame * 0.6) % 60}px, 0)`,
        }}
      />
      <div style={{ position: 'absolute', inset: 0, transformOrigin: '0 0', transform: camT }}>
        <svg width={W} height={H} style={{ overflow: 'visible' }}>
          <defs>
            <filter id="mglow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="6" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {countries.map((c, i) => {
            const isLit = lit.includes(String(c.id));
            const isActive = String(c.id) === activeCountry && frame >= stops[active].at - 4;
            return (
              <path
                key={i}
                d={path(c) || ''}
                fill={isActive ? 'rgba(255,43,58,0.38)' : isLit ? 'rgba(255,43,58,0.16)' : 'rgba(30,40,52,0.9)'}
                stroke={isActive ? C.red : 'rgba(120,170,200,0.45)'}
                strokeWidth={isActive ? 2.2 : 0.9}
                filter={isActive ? 'url(#mglow)' : undefined}
              />
            );
          })}
          {legs.map((d, i) => {
            const st = stops[i + 1].at - 22;
            const p = interpolate(frame, [st, stops[i + 1].at], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.inOut(Easing.cubic),
            });
            const ev = evolvePath(p, d);
            const len = getLength(d);
            return (
              <g key={i}>
                <path d={d} fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth={3} strokeDasharray="8 10" />
                <path
                  d={d}
                  fill="none"
                  stroke={C.gold}
                  strokeWidth={5}
                  strokeLinecap="round"
                  strokeDasharray={ev.strokeDasharray}
                  strokeDashoffset={ev.strokeDashoffset}
                  filter="url(#mglow)"
                  data-len={len}
                />
              </g>
            );
          })}
          {stops.map((s, i) => {
            const local = frame - s.at;
            if (local < -2) return null;
            const sp = spring({ frame: local + 2, fps, config: { damping: 10, stiffness: 200 } });
            const ring = ((frame - s.at) % 30) / 30;
            return (
              <g key={i} transform={`translate(${pts[i][0]},${pts[i][1]})`}>
                <circle r={10 + ring * 40} fill="none" stroke={C.gold} strokeWidth={2} opacity={(1 - ring) * 0.8} />
                <circle r={11 * sp} fill={C.gold} filter="url(#mglow)" />
                <circle r={4 * sp} fill="#fff" />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Photo card for current stop (screen space) */}
      {stops.map((s, i) => {
        const local = frame - s.at;
        const next = stops[i + 1];
        if (local < 0) return null;
        if (next && frame > next.at + 4) return null;
        const sp = spring({ frame: local, fps, config: { damping: 13, stiffness: 140, mass: 0.8 } });
        const leave = next ? interpolate(frame, [next.at - 4, next.at + 4], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 140,
              right: 140,
              top: 860,
              perspective: 1400,
            }}
          >
            <div
              style={{
                transform: `rotateY(${interpolate(sp, [0, 1], [-80, 0]) + leave * 70}deg) translateY(${interpolate(sp, [0, 1], [120, 0])}px) scale(${1 - leave * 0.2})`,
                opacity: sp * (1 - leave),
                borderRadius: 22,
                overflow: 'hidden',
                boxShadow: '0 40px 90px rgba(0,0,0,0.75), 0 0 0 3px rgba(255,201,74,0.7)',
                background: '#000',
              }}
            >
              <Img
                src={staticFile(`img/${s.img}`)}
                style={{
                  width: '100%',
                  height: 470,
                  objectFit: 'cover',
                  objectPosition: '50% 25%',
                  display: 'block',
                  transform: `scale(${1.12 - local * 0.002})`,
                  filter: 'contrast(1.1)',
                }}
              />
              <div style={{ padding: '18px 26px 22px', background: 'linear-gradient(180deg,#14100a,#000)' }}>
                <div style={{ fontFamily: HEAD, fontSize: 72, color: '#fff', lineHeight: 1 }}>{s.name}</div>
                <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 30, color: C.gold, letterSpacing: 4, marginTop: 8 }}>
                  {s.sub}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
