import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig, delayRender, continueRender} from 'remotion';
import {geoOrthographic, geoPath, geoGraticule10, geoInterpolate, geoDistance} from 'd3-geo';
import {feature} from 'topojson-client';
import type {FeatureCollection, Geometry} from 'geojson';
import {C, FONT_UI, FONT_DISPLAY, easeInOut, ease} from './core';

export const TASHKENT: [number, number] = [69.2401, 41.2995];
export const TSUKUBA: [number, number] = [140.1023, 36.0835];
export const DIST_KM = Math.round((geoDistance(TASHKENT, TSUKUBA) * 6371) / 10) * 10;

let cache: FeatureCollection<Geometry, {name: string}> | null = null;

const useWorld = () => {
  const [data, setData] = React.useState(cache);
  const [handle] = React.useState(() => (cache ? null : delayRender('world topojson')));
  React.useEffect(() => {
    if (cache) return;
    fetch(staticFile('data/world-110m.json'))
      .then((r) => r.json())
      .then((topo) => {
        cache = feature(topo, topo.objects.countries) as unknown as FeatureCollection<Geometry, {name: string}>;
        setData(cache);
        if (handle !== null) continueRender(handle);
      });
  }, [handle]);
  return data;
};

type Pin = {at: number; coord: [number, number]; label: string; color?: string};

export const Globe: React.FC<{
  rotFrom: [number, number];
  rotTo: [number, number];
  scaleFrom: number;
  scaleTo: number;
  moveDur: number;
  highlight: string[]; // country names
  pins: Pin[];
  arc?: {from: [number, number]; to: [number, number]; at: number; dur: number};
  cy?: number;
}> = ({rotFrom, rotTo, scaleFrom, scaleTo, moveDur, highlight, pins, arc, cy = 900}) => {
  const world = useWorld();
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const t = frame / fps;
  const p = interpolate(t, [0, moveDur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut});
  const lon = interpolate(p, [0, 1], [rotFrom[0], rotTo[0]]);
  const lat = interpolate(p, [0, 1], [rotFrom[1], rotTo[1]]);
  const scale = interpolate(p, [0, 1], [scaleFrom, scaleTo]);

  const projection = useMemo(() => geoOrthographic().clipAngle(90).precision(0.3), []);
  projection.scale(scale).translate([width / 2, cy]).rotate([-lon, -lat, 0]);
  const path = geoPath(projection);
  const grat = useMemo(() => geoGraticule10(), []);

  if (!world) return null;

  const arcPts: Array<[number, number]> = [];
  let planePos: [number, number] | null = null;
  let planeAngle = 0;
  if (arc) {
    const ip = geoInterpolate(arc.from, arc.to);
    const ap = interpolate(t, [arc.at, arc.at + arc.dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut});
    const N = 80;
    for (let i = 0; i <= N * ap; i++) {
      const g = ip(i / N);
      const xy = projection(g);
      if (xy) {
        // lift the arc above the surface (parabolic height) for a 2.5D feel
        const h = Math.sin((i / N) * Math.PI) * 120;
        arcPts.push([xy[0], xy[1] - h]);
      }
    }
    if (arcPts.length > 1 && ap > 0 && ap < 1) {
      const a = arcPts[arcPts.length - 1];
      const b = arcPts[arcPts.length - 2];
      planePos = a;
      planeAngle = (Math.atan2(a[1] - b[1], a[0] - b[0]) * 180) / Math.PI;
    }
  }

  return (
    <AbsoluteFill>
      <svg width={width} height={1920} style={{position: 'absolute'}}>
        <defs>
          <radialGradient id="ocean" cx="40%" cy="35%" r="75%">
            <stop offset="0%" stopColor="#173a5a" />
            <stop offset="60%" stopColor="#0b1d33" />
            <stop offset="100%" stopColor="#050b14" />
          </radialGradient>
          <radialGradient id="atmo" cx="50%" cy="50%" r="50%">
            <stop offset="85%" stopColor="rgba(95,208,255,0)" />
            <stop offset="93%" stopColor="rgba(95,208,255,0.35)" />
            <stop offset="100%" stopColor="rgba(95,208,255,0)" />
          </radialGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="8" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle cx={width / 2} cy={cy} r={scale * 1.12} fill="url(#atmo)" />
        <path d={path({type: 'Sphere'}) ?? ''} fill="url(#ocean)" stroke="rgba(95,208,255,0.5)" strokeWidth={2} />
        <path d={path(grat) ?? ''} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={1.2} />
        {world.features.map((ft, i) => {
          const hi = highlight.includes(ft.properties.name);
          return (
            <path
              key={i}
              d={path(ft) ?? ''}
              fill={hi ? (ft.properties.name === 'Japan' ? C.accent2 : C.accent) : 'rgba(170,190,210,0.22)'}
              stroke={hi ? '#fff' : 'rgba(255,255,255,0.18)'}
              strokeWidth={hi ? 2.5 : 0.8}
              filter={hi ? 'url(#glow)' : undefined}
            />
          );
        })}
        {arcPts.length > 1 ? (
          <>
            <polyline points={arcPts.map((q) => q.join(',')).join(' ')} fill="none" stroke={C.white} strokeWidth={7} strokeDasharray="2 16" strokeLinecap="round" filter="url(#glow)" />
          </>
        ) : null}
        {planePos ? (
          <g transform={`translate(${planePos[0]},${planePos[1]}) rotate(${planeAngle + 90})`}>
            {/* simple airliner glyph */}
            <path d="M0,-34 C4,-34 6,-28 6,-20 L6,-6 L34,8 L34,16 L6,8 L6,22 L14,30 L14,36 L0,32 L-14,36 L-14,30 L-6,22 L-6,8 L-34,16 L-34,8 L-6,-6 L-6,-20 C-6,-28 -4,-34 0,-34 Z" fill="#fff" filter="url(#glow)" />
          </g>
        ) : null}
      </svg>
      {pins.map((pin, i) => {
        const xy = projection(pin.coord);
        if (!xy) return null;
        const pp = interpolate(t, [pin.at, pin.at + 0.35], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
        const pulse = (t - pin.at) % 1;
        const col = pin.color ?? C.accent;
        return (
          <div key={i} style={{position: 'absolute', left: xy[0], top: xy[1], opacity: pp}}>
            <div
              style={{
                position: 'absolute',
                left: -60,
                top: -60,
                width: 120,
                height: 120,
                borderRadius: 60,
                border: `4px solid ${col}`,
                transform: `scale(${t > pin.at ? 0.3 + pulse * 1.2 : 0})`,
                opacity: 1 - pulse,
              }}
            />
            <div style={{position: 'absolute', left: -14, top: -14, width: 28, height: 28, borderRadius: 14, background: '#fff', border: `6px solid ${col}`, boxShadow: `0 0 30px ${col}`}} />
            <div
              style={{
                position: 'absolute',
                left: -300,
                width: 600,
                top: -120 - (1 - pp) * 30,
                textAlign: 'center',
                fontFamily: FONT_DISPLAY,
                fontWeight: 900,
                fontSize: 64,
                color: '#fff',
                letterSpacing: 2,
                textShadow: '0 4px 20px rgba(0,0,0,0.8)',
              }}
            >
              {pin.label}
            </div>
          </div>
        );
      })}
      <div style={{position: 'absolute', bottom: 520, width: '100%', textAlign: 'center', fontFamily: FONT_UI, fontWeight: 500, fontSize: 26, color: 'rgba(255,255,255,0.45)', letterSpacing: 3}}>
        {`${lat.toFixed(2)}° N  ·  ${lon.toFixed(2)}° E`}
      </div>
    </AbsoluteFill>
  );
};
