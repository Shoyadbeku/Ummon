import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {geoGraticule10, geoInterpolate, geoMercator, geoOrthographic, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import type {Feature, FeatureCollection, Geometry} from 'geojson';
import world50 from 'world-atlas/countries-50m.json';
import world110 from 'world-atlas/countries-110m.json';
import {FONT} from '../fonts';
import {C, Check, Cross, clamp, ease, easeInOut} from './base';

const UZ_ID = '860';
const TASHKENT: [number, number] = [69.24, 41.31];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries50 = feature(world50 as any, (world50 as any).objects.countries) as unknown as FeatureCollection<Geometry, {name: string}>;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries110 = feature(world110 as any, (world110 as any).objects.countries) as unknown as FeatureCollection<Geometry, {name: string}>;
const uz50 = countries50.features.find((x) => String(x.id) === UZ_ID) as Feature<Geometry>;

/* ------------------------------------------------------------------ */
/* ID card: mystery (redacted) → reveal                                */
/* ------------------------------------------------------------------ */
export const IdCard: React.FC<{revealZilola?: number; revealMusayeva?: number; mystery?: boolean; y?: number}> = ({
  revealZilola = 9999,
  revealMusayeva = 9999,
  mystery = false,
  y = 250,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 14, mass: 0.8, stiffness: 120}});
  const r1 = interpolate(frame, [revealZilola, revealZilola + 9], [0, 1], {...clamp, easing: ease});
  const r2 = interpolate(frame, [revealMusayeva, revealMusayeva + 9], [0, 1], {...clamp, easing: ease});
  const glitch = mystery && frame % 23 < 2;
  const photoBlur = mystery ? 22 : interpolate(frame, [revealZilola - 6, revealZilola + 6], [10, 0], clamp);
  const qPulse = 1 + 0.08 * Math.sin(frame / 4);
  const scan = (frame * 14) % 520;

  const Field: React.FC<{label: string; children: React.ReactNode}> = ({label, children}) => (
    <div style={{marginBottom: 22}}>
      <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 24, letterSpacing: 4, color: 'rgba(255,255,255,.55)'}}>{label}</div>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 52, color: '#fff', lineHeight: 1.05, marginTop: 4}}>{children}</div>
    </div>
  );

  const Redact: React.FC<{text: string; r: number; w: number}> = ({text, r, w}) => (
    <div style={{position: 'relative', display: 'inline-block', height: 60, minWidth: w}}>
      <span style={{color: C.green, textShadow: `0 0 ${30 * r}px ${C.green}`, opacity: r, display: 'inline-block', transform: `scale(${0.8 + 0.2 * r})`, transformOrigin: 'left'}}>
        {text}
      </span>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 6,
          height: 50,
          width: w,
          background: 'repeating-linear-gradient(90deg,#111 0 18px,#1c1c22 18px 22px)',
          border: '2px solid rgba(255,255,255,.12)',
          borderRadius: 6,
          transformOrigin: 'right',
          transform: `scaleX(${1 - r})`,
        }}
      />
    </div>
  );

  return (
    <div
      style={{
        position: 'absolute',
        top: y,
        left: 70,
        width: 940,
        transform: `translateY(${(1 - enter) * 160}px) rotateX(${(1 - enter) * 30}deg) scale(${0.9 + 0.1 * enter}) translateX(${glitch ? 12 : 0}px)`,
        opacity: enter,
        perspective: 1200,
      }}
    >
      <div
        style={{
          position: 'relative',
          borderRadius: 34,
          padding: 34,
          background: 'linear-gradient(135deg, rgba(25,22,40,.88), rgba(10,10,18,.92))',
          border: `3px solid ${C.gold}`,
          boxShadow: `0 30px 90px rgba(0,0,0,.6), 0 0 60px rgba(255,200,61,.25), inset 0 0 40px rgba(255,200,61,.08)`,
          overflow: 'hidden',
          backdropFilter: 'blur(8px)',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 26}}>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 30, letterSpacing: 6, color: C.gold}}>SHAXS MAʼLUMOTI</div>
          <div style={{display: 'flex', gap: 10}}>
            {[0, 1, 2].map((i) => (
              <div key={i} style={{width: 18, height: 18, borderRadius: 9, background: i === 0 ? C.red : 'rgba(255,255,255,.25)', opacity: i === 0 ? 0.5 + 0.5 * Math.sin(frame / 5) : 1}} />
            ))}
          </div>
        </div>
        <div style={{display: 'flex', gap: 34}}>
          <div style={{position: 'relative', width: 300, height: 380, borderRadius: 20, overflow: 'hidden', flexShrink: 0, border: '2px solid rgba(255,255,255,.2)'}}>
            <Img
              src={staticFile('media/img/shahzoda_2012.jpg')}
              style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '66% 20%', transform: 'scale(1.6)', transformOrigin: '66% 25%', filter: `blur(${photoBlur}px) ${mystery ? 'grayscale(1) brightness(.6)' : 'contrast(1.05)'}`}}
            />
            {mystery ? (
              <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
                <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 200, color: C.gold, transform: `scale(${qPulse})`, textShadow: `0 0 50px ${C.gold}`}}>?</div>
              </AbsoluteFill>
            ) : null}
          </div>
          <div style={{flex: 1, paddingTop: 6}}>
            <Field label="TAXALLUSI">
              <span style={{color: C.gold}}>SHAHZODA</span>
            </Field>
            <Field label="ASL ISMI">
              <Redact text="ZILOLA" r={r1} w={250} />
              <br />
              <Redact text="MUSAYEVA" r={r2} w={330} />
            </Field>
            <Field label="SOHASI">
              <span style={{fontSize: 34}}>ESTRADA</span>
            </Field>
          </div>
        </div>
        {/* scan line */}
        <div style={{position: 'absolute', left: 0, right: 0, top: 90 + scan, height: 3, background: `linear-gradient(90deg, transparent, ${mystery ? C.accent : C.gold}, transparent)`, opacity: 0.55}} />
        {/* stamp */}
        {!mystery ? (
          <div
            style={{
              position: 'absolute',
              right: 40,
              bottom: 34,
              padding: '10px 20px',
              border: `5px solid ${C.green}`,
              borderRadius: 12,
              color: C.green,
              fontFamily: FONT,
              fontWeight: 900,
              fontSize: 34,
              letterSpacing: 3,
              transform: `rotate(-12deg) scale(${interpolate(frame, [revealMusayeva + 6, revealMusayeva + 14], [2.2, 1], {...clamp, easing: ease})})`,
              opacity: interpolate(frame, [revealMusayeva + 6, revealMusayeva + 10], [0, 1], clamp),
            }}
          >
            HAQIQIY ISM
          </div>
        ) : null}
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Uzbekistan map draw-on                                              */
/* ------------------------------------------------------------------ */
export const UzMap: React.FC<{y?: number}> = ({y = 260}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const Wm = 980;
  const Hm = 640;
  const {uzPath, neighbours, tash} = useMemo(() => {
    const proj = geoMercator().fitExtent([[40, 40], [Wm - 40, Hm - 40]], uz50 as any);
    const path = geoPath(proj);
    const nb = countries50.features.filter((c) => ['398', '417', '762', '795', '004'].includes(String(c.id))).map((c) => path(c) || '');
    return {uzPath: path(uz50) || '', neighbours: nb, tash: proj(TASHKENT) as [number, number]};
  }, []);
  const draw = interpolate(frame, [0, 26], [0, 1], {...clamp, easing: easeInOut});
  const fill = interpolate(frame, [18, 34], [0, 1], clamp);
  const pin = spring({frame: frame - 22, fps, config: {damping: 9, mass: 0.6}});
  const ring = (frame % 30) / 30;
  const label = spring({frame: frame - 14, fps, config: {damping: 14}});
  const zoom = interpolate(frame, [0, 60], [1.0, 1.08]);
  return (
    <div style={{position: 'absolute', top: y, left: 50, width: Wm, height: Hm + 220, transform: `scale(${zoom})`}}>
      <svg width={Wm} height={Hm} style={{overflow: 'visible'}}>
        <defs>
          <linearGradient id="uzfill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#1EB5E8" />
            <stop offset="0.5" stopColor="#FFFFFF" />
            <stop offset="1" stopColor="#1EB53A" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="8" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {neighbours.map((d, i) => (
          <path key={i} d={d} fill="rgba(255,255,255,.04)" stroke="rgba(255,255,255,.18)" strokeWidth={2} opacity={draw} />
        ))}
        <path d={uzPath} fill="url(#uzfill)" opacity={fill * 0.55} />
        <path d={uzPath} fill="none" stroke={C.gold} strokeWidth={6} filter="url(#glow)" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} strokeLinejoin="round" />
        <g transform={`translate(${tash[0]}, ${tash[1]})`}>
          <circle r={14 + ring * 70} fill="none" stroke={C.gold} strokeWidth={4} opacity={(1 - ring) * pin} />
          <circle r={16 * pin} fill={C.gold} />
          <path d="M0 -60 l7 18 h19 l-15 11 l6 19 l-17 -12 l-17 12 l6 -19 l-15 -11 h19 z" transform={`translate(0, ${-8 * pin}) scale(${pin})`} fill="#fff" stroke={C.gold} strokeWidth={3} />
        </g>
      </svg>
      <div
        style={{
          textAlign: 'center',
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 92,
          letterSpacing: 8,
          color: '#fff',
          marginTop: 10,
          transform: `translateY(${(1 - label) * 40}px)`,
          opacity: label,
          textShadow: '0 8px 30px rgba(0,0,0,.7)',
        }}
      >
        OʻZBEKISTON
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Orthographic globe with outgoing arcs                               */
/* ------------------------------------------------------------------ */
const DESTS: [number, number][] = [
  [74.6, 42.87],
  [76.9, 43.24],
  [37.62, 55.75],
  [28.98, 41.01],
  [68.78, 38.56],
  [55.27, 25.2],
  [126.98, 37.57],
  [13.4, 52.52],
];

export const Globe: React.FC<{arcsAt?: number; size?: number; y?: number}> = ({arcsAt = 28, size = 430, y = 640}) => {
  const frame = useCurrentFrame();
  const rotT = interpolate(frame, [0, 34], [0, 1], {...clamp, easing: easeInOut});
  const lon = interpolate(rotT, [0, 1], [-10, TASHKENT[0]]) + interpolate(frame, [34, 120], [0, 14], clamp);
  const lat = interpolate(rotT, [0, 1], [10, 34]);
  const proj = geoOrthographic().scale(size).translate([540, y]).rotate([-lon, -lat]).clipAngle(90);
  const path = geoPath(proj);
  const grat = geoGraticule10();
  const tash = proj(TASHKENT);
  const ring = (frame % 24) / 24;
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920}>
        <defs>
          <radialGradient id="ocean" cx="40%" cy="35%" r="70%">
            <stop offset="0" stopColor="#1b3b6f" />
            <stop offset="1" stopColor="#060b1c" />
          </radialGradient>
          <radialGradient id="atmo" cx="50%" cy="50%" r="50%">
            <stop offset="0.86" stopColor="rgba(94,231,255,0)" />
            <stop offset="0.93" stopColor="rgba(94,231,255,.45)" />
            <stop offset="1" stopColor="rgba(94,231,255,0)" />
          </radialGradient>
        </defs>
        <circle cx={540} cy={y} r={size * 1.16} fill="url(#atmo)" />
        <circle cx={540} cy={y} r={size} fill="url(#ocean)" />
        <path d={path(grat) || ''} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth={1.5} />
        {countries110.features.map((c, i) => {
          const isUz = String(c.id) === UZ_ID;
          return <path key={i} d={path(c) || ''} fill={isUz ? C.gold : '#2c4a7c'} stroke={isUz ? '#fff' : 'rgba(255,255,255,.25)'} strokeWidth={isUz ? 3 : 0.8} />;
        })}
        {DESTS.map((d, i) => {
          const start = arcsAt + i * 3;
          const p = interpolate(frame, [start, start + 18], [0, 1], {...clamp, easing: ease});
          if (p <= 0) return null;
          const interp = geoInterpolate(TASHKENT, d);
          const pts = new Array(40).fill(0).map((_, k) => interp((k / 39) * p));
          const line = path({type: 'LineString', coordinates: pts} as any) || '';
          const end = proj(pts[pts.length - 1]);
          return (
            <g key={i}>
              <path d={line} fill="none" stroke={C.gold} strokeWidth={10} opacity={0.25} strokeLinecap="round" />
              <path d={line} fill="none" stroke="#fff" strokeWidth={4} strokeLinecap="round" />
              {end && p > 0.98 ? <circle cx={end[0]} cy={end[1]} r={9} fill={C.accent} /> : null}
            </g>
          );
        })}
        {tash ? (
          <g>
            <circle cx={tash[0]} cy={tash[1]} r={10 + ring * 50} fill="none" stroke={C.gold} strokeWidth={4} opacity={1 - ring} />
            <circle cx={tash[0]} cy={tash[1]} r={11} fill="#fff" />
          </g>
        ) : null}
      </svg>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ */
/* Animated number counter                                             */
/* ------------------------------------------------------------------ */
export const Counter: React.FC<{to: number; dur?: number; y?: number; label: string}> = ({to, dur = 26, y = 330, label}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: ease});
  const n = Math.round(to * p);
  const txt = n.toLocaleString('en-US').replace(/,/g, ' ');
  const done = spring({frame: frame - dur, fps, config: {damping: 8, mass: 0.5}});
  const enter = spring({frame, fps, config: {damping: 14}});
  return (
    <div style={{position: 'absolute', top: y, left: 0, right: 0, textAlign: 'center', opacity: enter}}>
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 160,
          color: C.gold,
          letterSpacing: -4,
          fontVariantNumeric: 'tabular-nums',
          transform: `scale(${1 + 0.08 * done * Math.max(0, 1 - (frame - dur) / 20)})`,
          textShadow: `0 0 50px rgba(255,200,61,.6), 0 12px 40px rgba(0,0,0,.7)`,
        }}
      >
        {txt}
        <span style={{opacity: done}}>+</span>
      </div>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 58, color: '#fff', letterSpacing: 6, marginTop: 6, textShadow: '0 6px 24px rgba(0,0,0,.8)'}}>{label}</div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Rising popularity graph (illustrative, no data values)               */
/* ------------------------------------------------------------------ */
export const RiseGraph: React.FC<{y?: number}> = ({y = 260}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [4, 34], [0, 1], {...clamp, easing: easeInOut});
  const pts: [number, number][] = [
    [0, 420], [110, 400], [200, 410], [290, 350], [380, 365], [470, 280], [560, 300], [650, 200], [740, 150], [840, 40],
  ];
  const d = pts.map((q, i) => `${i ? 'L' : 'M'}${q[0]},${q[1]}`).join(' ');
  const area = `${d} L840,470 L0,470 Z`;
  const tip = pts[Math.min(pts.length - 1, Math.floor(p * (pts.length - 1)))];
  const head = spring({frame: frame - 2, fps, config: {damping: 13}});
  return (
    <div style={{position: 'absolute', top: y, left: 120, width: 840}}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 72, color: '#fff', letterSpacing: 4, marginBottom: 20, opacity: head, transform: `translateX(${(1 - head) * -60}px)`, textShadow: '0 6px 24px rgba(0,0,0,.8)'}}>
        MASHHURLIK <span style={{color: C.green}}>▲</span>
      </div>
      <svg width={840} height={470} style={{overflow: 'visible'}}>
        <defs>
          <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(61,255,143,.55)" />
            <stop offset="1" stopColor="rgba(61,255,143,0)" />
          </linearGradient>
          <clipPath id="gc">
            <rect x={0} y={-50} width={840 * p + 4} height={600} />
          </clipPath>
        </defs>
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1={0} x2={840} y1={470 - i * 140} y2={470 - i * 140} stroke="rgba(255,255,255,.15)" strokeWidth={2} strokeDasharray="8 10" />
        ))}
        <g clipPath="url(#gc)">
          <path d={area} fill="url(#ga)" />
          <path d={d} fill="none" stroke={C.green} strokeWidth={10} strokeLinejoin="round" strokeLinecap="round" style={{filter: `drop-shadow(0 0 14px ${C.green})`}} />
        </g>
        <circle cx={tip[0]} cy={tip[1]} r={16} fill="#fff" stroke={C.green} strokeWidth={6} opacity={p > 0.02 ? 1 : 0} />
      </svg>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Career timeline chip: GURUH → YAKKAXON                               */
/* ------------------------------------------------------------------ */
export const TimelineChip: React.FC<{switchAt: number; outAt: number}> = ({switchAt, outAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 14}});
  const exit = interpolate(frame, [outAt, outAt + 8], [1, 0], clamp);
  const prog = interpolate(frame, [switchAt, switchAt + 18], [0, 1], {...clamp, easing: easeInOut});
  const Node: React.FC<{label: string; on: number; x: number}> = ({label, on, x}) => (
    <div style={{position: 'absolute', left: x, top: 0, transform: 'translateX(-50%)', textAlign: 'center'}}>
      <div style={{width: 40, height: 40, margin: '0 auto', borderRadius: 20, background: on > 0.5 ? C.gold : '#222', border: `5px solid ${C.gold}`, boxShadow: on > 0.5 ? `0 0 30px ${C.gold}` : 'none', transform: `scale(${1 + 0.25 * on})`}} />
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 36, marginTop: 12, letterSpacing: 2, color: on > 0.5 ? C.gold : 'rgba(255,255,255,.7)'}}>{label}</div>
    </div>
  );
  return (
    <div style={{position: 'absolute', top: 190, left: 140, width: 800, height: 130, opacity: enter * exit, transform: `translateY(${(1 - enter) * -50}px)`}}>
      <div style={{position: 'absolute', top: 17, left: 80, width: 640, height: 6, background: 'rgba(255,255,255,.25)', borderRadius: 3}} />
      <div style={{position: 'absolute', top: 17, left: 80, width: 640 * prog, height: 6, background: C.gold, borderRadius: 3, boxShadow: `0 0 16px ${C.gold}`}} />
      <Node label="GURUH" on={1 - prog * 0.9} x={80} />
      <Node label="YAKKAXON" on={prog} x={720} />
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Split screen: birth name ✗ vs stage name ✓                          */
/* ------------------------------------------------------------------ */
export const NameVs: React.FC<{strikeAt: number; stageAt: number; checkAt: number}> = ({strikeAt, stageAt, checkAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame, fps, config: {damping: 14}});
  const strike = interpolate(frame, [strikeAt, strikeAt + 7], [0, 1], {...clamp, easing: ease});
  const xP = interpolate(frame, [strikeAt + 2, strikeAt + 12], [0, 1], clamp);
  const b = spring({frame: frame - stageAt, fps, config: {damping: 12}});
  const ck = interpolate(frame, [checkAt, checkAt + 12], [0, 1], clamp);
  const dim = interpolate(frame, [strikeAt, strikeAt + 10], [1, 0.55], clamp);
  return (
    <>
      <div style={{position: 'absolute', top: 330, left: 0, right: 0, textAlign: 'center', opacity: a * dim, transform: `translateY(${(1 - a) * -40}px)`}}>
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 34, letterSpacing: 6, color: 'rgba(255,255,255,.75)'}}>TUGʻILGANDAGI ISMI</div>
        <div style={{position: 'relative', display: 'inline-block', marginTop: 10}}>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 96, color: '#fff', letterSpacing: -1, textShadow: '0 8px 30px rgba(0,0,0,.8)'}}>ZILOLA MUSAYEVA</div>
          <div style={{position: 'absolute', left: -10, right: -10, top: '50%', height: 12, background: C.red, borderRadius: 6, transformOrigin: 'left', transform: `scaleX(${strike}) rotate(-3deg)`, boxShadow: `0 0 20px ${C.red}`}} />
        </div>
        <div style={{marginTop: 18, display: 'flex', justifyContent: 'center', transform: `scale(${0.6 + 0.4 * xP})`, opacity: xP}}>
          <Cross progress={xP} size={100} />
        </div>
      </div>
      <div style={{position: 'absolute', top: 1330, left: 0, right: 0, textAlign: 'center', opacity: b, transform: `translateY(${(1 - b) * 60}px)`}}>
        <div style={{display: 'inline-flex', alignItems: 'center', gap: 22, padding: '14px 34px', borderRadius: 24, background: 'rgba(10,10,18,.72)', border: `3px solid ${C.gold}`, boxShadow: `0 0 40px rgba(255,200,61,.35)`}}>
          <div style={{textAlign: 'left'}}>
            <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 28, letterSpacing: 5, color: 'rgba(255,255,255,.8)'}}>SAHNADAGI TAXALLUSI</div>
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 92, color: C.gold, lineHeight: 1, textShadow: `0 0 30px rgba(255,200,61,.6)`}}>SHAHZODA</div>
          </div>
          <div style={{transform: `scale(${0.6 + 0.4 * ck})`, opacity: ck}}>
            <Check progress={ck} size={96} />
          </div>
        </div>
      </div>
    </>
  );
};

/* ------------------------------------------------------------------ */
/* CTA: spinning vinyl with photo label + comment prompt               */
/* ------------------------------------------------------------------ */
export const VinylCTA: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 15, mass: 0.9}});
  const rot = frame * 5.5;
  const R = 330;
  const pill = spring({frame: frame - 16, fps, config: {damping: 10, mass: 0.6}});
  const bob = Math.sin(frame / 5) * 8;
  const notes = new Array(6).fill(0).map((_, i) => {
    const lf = (frame + i * 9) % 54;
    return {x: 540 + Math.sin(i * 2.1) * 360, y: 760 - lf * 9, o: interpolate(lf, [0, 10, 44, 54], [0, 1, 1, 0]), s: 0.7 + random(`n${i}`) * 0.6};
  });
  return (
    <AbsoluteFill>
      {notes.map((n, i) => (
        <div key={i} style={{position: 'absolute', left: n.x, top: n.y, fontSize: 70 * n.s, color: C.gold, opacity: n.o * enter, fontFamily: 'serif', textShadow: `0 0 20px ${C.gold}`}}>
          {i % 2 ? '♪' : '♫'}
        </div>
      ))}
      <div style={{position: 'absolute', left: 540 - R, top: 300, width: R * 2, height: R * 2, transform: `scale(${0.4 + 0.6 * enter}) rotate(${rot}deg)`, opacity: enter}}>
        <svg width={R * 2} height={R * 2}>
          <defs>
            <radialGradient id="vin" cx="50%" cy="50%" r="50%">
              <stop offset="0.3" stopColor="#141418" />
              <stop offset="1" stopColor="#050507" />
            </radialGradient>
            <linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0.3" stopColor="rgba(255,255,255,0)" />
              <stop offset="0.5" stopColor="rgba(255,255,255,.22)" />
              <stop offset="0.7" stopColor="rgba(255,255,255,0)" />
            </linearGradient>
            <clipPath id="lbl">
              <circle cx={R} cy={R} r={R * 0.36} />
            </clipPath>
          </defs>
          <circle cx={R} cy={R} r={R} fill="url(#vin)" />
          {new Array(22).fill(0).map((_, i) => (
            <circle key={i} cx={R} cy={R} r={R * 0.4 + i * 9} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth={2} />
          ))}
          <circle cx={R} cy={R} r={R} fill="url(#sheen)" />
          <image href={staticFile('media/img/shahzoda_2012.jpg')} x={R - 567} y={R - 190} width={900} height={600} preserveAspectRatio="none" clipPath="url(#lbl)" />
          <circle cx={R} cy={R} r={R * 0.36} fill="none" stroke={C.gold} strokeWidth={6} />
          <circle cx={R} cy={R} r={10} fill="#000" />
        </svg>
      </div>
      <div style={{position: 'absolute', top: 1010 + bob, left: 0, right: 0, display: 'flex', justifyContent: 'center', transform: `scale(${pill})`, opacity: Math.min(1, pill * 2)}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 18, background: '#fff', color: C.ink, padding: '20px 40px', borderRadius: 999, fontFamily: FONT, fontWeight: 900, fontSize: 46, boxShadow: '0 20px 60px rgba(0,0,0,.5)'}}>
          <svg width="56" height="56" viewBox="0 0 24 24">
            <path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" fill={C.goldDeep} />
            <circle cx="8" cy="11" r="1.5" fill="#fff" />
            <circle cx="12" cy="11" r="1.5" fill="#fff" />
            <circle cx="16" cy="11" r="1.5" fill="#fff" />
          </svg>
          IZOHLARDA YOZING
        </div>
      </div>
    </AbsoluteFill>
  );
};
