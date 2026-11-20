import React, {useMemo} from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing} from 'remotion';
import {geoOrthographic, geoPath, geoInterpolate, geoGraticule10} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-110m.json';
import {C, HEAD, BODY, ease, pop, sec, textStroke} from './theme';
import {Kinetic} from './Overlays';
import type {Shot} from './Main';

type P = {shot: Shot; index: number};
const rel = (shot: Shot, t: number) => Math.round((t - shot.start) * 30);

// ---------- shared background ----------
const BG: React.FC<{file?: string; dark?: number}> = ({file, dark = 0.55}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, 300], [1.05, 1.18]);
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {file ? (
        <AbsoluteFill style={{transform: `scale(${z})`}}>
          <OffthreadVideo src={staticFile(file)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at ${50 + Math.sin(f / 40) * 20}% ${40 + Math.cos(f / 50) * 10}%, #1b2440 0%, #0a0e1a 45%, #05070c 100%)`,
          }}
        />
      )}
      <AbsoluteFill style={{background: `rgba(4,6,12,${dark})`}} />
      {/* subtle moving grid */}
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px)',
          backgroundSize: '90px 90px', backgroundPosition: `0px ${f * 0.6}px`,
        }}
      />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.7) 100%)'}} />
    </AbsoluteFill>
  );
};

const Title: React.FC<{text: string; top?: number; delay?: number; color?: string}> = ({text, top = 60, delay = 0, color = C.gold}) => {
  const f = useCurrentFrame();
  const p = ease(f, delay, delay + 14);
  return (
    <div style={{position: 'absolute', top, left: 0, right: 0, textAlign: 'center', opacity: p, transform: `translateY(${(1 - p) * 30}px)`}}>
      <div style={{display: 'inline-block', fontFamily: HEAD, fontWeight: 800, fontSize: 40, letterSpacing: 8, color, borderBottom: `4px solid ${color}`, paddingBottom: 8}}>
        {text}
      </div>
    </div>
  );
};

const Chip: React.FC<{text: string; p: number; color?: string; size?: number; style?: React.CSSProperties; active?: boolean}> = ({text, p, color = C.gold, size = 46, style, active = true}) => (
  <div
    style={{
      fontFamily: HEAD, fontWeight: 900, fontSize: size, color: '#fff', padding: '18px 30px', borderRadius: 20,
      background: active ? 'rgba(10,14,24,0.82)' : 'rgba(10,14,24,0.5)', border: `3px solid ${active ? color : 'rgba(255,255,255,0.2)'}`,
      boxShadow: active ? `0 0 40px ${color}44, 0 20px 40px rgba(0,0,0,0.5)` : 'none',
      transform: `scale(${0.4 + 0.6 * p})`, opacity: Math.min(1, p * 1.5), whiteSpace: 'nowrap', lineHeight: 1.05, ...style,
    }}
  >
    {text}
  </div>
);

// ---------- individual graphics ----------
const Who: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times, stamp, stampTime, bgFile} = shot.props;
  const st = stamp ? rel(shot, stampTime) : 99999;
  const sp = pop(f, st, 9, 260, 0.6);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.62} />
      <AbsoluteFill style={{flexDirection: 'row', flexWrap: 'wrap', alignContent: 'flex-start', alignItems: 'center', justifyContent: 'center', padding: '200px 80px 0', gap: 30}}>
        {items.map((it: string, i: number) => {
          const at = rel(shot, times[i]) - 2;
          const p = pop(f, at, 11, 170);
          const strike = ease(f, st + 4 + i * 3, st + 12 + i * 3);
          const active = f >= at && (i === items.length - 1 || f < rel(shot, times[i + 1]) - 2);
          return (
            <div key={i} style={{position: 'relative', transform: `translateX(${(1 - p) * (i % 2 ? 300 : -300)}px)`, opacity: Math.min(1, p * 1.4)}}>
              <div
                style={{
                  fontFamily: HEAD, fontWeight: 900, fontSize: items.length > 3 ? 68 : 84, color: active && !stamp ? C.gold : '#fff',
                  padding: '6px 34px', background: active && !stamp ? 'rgba(255,200,61,0.12)' : 'rgba(0,0,0,0.35)', borderRadius: 16,
                  transform: `scale(${active && !stamp ? 1.06 : 1})`, ...textStroke(3, 'rgba(0,0,0,0.5)'),
                }}
              >
                {it}
                {stamp ? '' : '?'}
              </div>
              <div style={{position: 'absolute', left: 10, right: 10, top: '50%', height: 12, background: C.red, transform: `scaleX(${strike})`, transformOrigin: 'left', borderRadius: 6}} />
            </div>
          );
        })}
        {stamp ? (
          <div
            style={{
              marginTop: 40, transform: `rotate(-5deg) scale(${2.3 - 1.3 * sp})`, opacity: Math.min(1, sp * 2), border: `10px solid ${C.red}`,
              color: C.red, fontFamily: HEAD, fontWeight: 900, fontSize: 80, padding: '8px 30px', borderRadius: 16, background: 'rgba(0,0,0,0.45)',
            }}
          >
            {stamp}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Factors: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {title, items, times, bgFile} = shot.props;
  const cx = 960, cy = 440, R = 560, RY = 320;
  const n = items.length;
  const cp = pop(f, 0, 12, 140);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.68} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {items.map((_: string, i: number) => {
          const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
          const x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * RY;
          const at = rel(shot, times[i]) - 2;
          const p = ease(f, at, at + 12);
          return <line key={i} x1={cx} y1={cy} x2={cx + (x - cx) * p} y2={cy + (y - cy) * p} stroke={C.gold} strokeWidth={4} strokeDasharray="10 10" strokeDashoffset={-f * 1.5} opacity={0.8} />;
        })}
      </svg>
      <div
        style={{
          position: 'absolute', left: cx - 150, top: cy - 150, width: 300, height: 300, borderRadius: 150, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'radial-gradient(circle, rgba(255,200,61,0.35), rgba(10,14,24,0.95) 70%)', border: `4px solid ${C.gold}`, transform: `scale(${cp})`,
          boxShadow: `0 0 ${60 + Math.sin(f / 6) * 20}px ${C.gold}66`, textAlign: 'center',
        }}
      >
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 40, color: '#fff', lineHeight: 1.1, padding: 20}}>{title}</div>
      </div>
      {items.map((it: string, i: number) => {
        const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
        const x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * RY;
        const at = rel(shot, times[i]) - 2;
        const p = pop(f, at, 11, 170);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%,-50%)'}}>
            <Chip text={it} p={p} size={it.length > 14 ? 30 : 38} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Question: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {text, bgFile} = shot.props;
  const qp = pop(f, 6, 8, 120);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.55} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -100}}>
        <div style={{position: 'absolute', fontFamily: HEAD, fontWeight: 900, fontSize: 760, color: 'rgba(255,200,61,0.10)', transform: `scale(${0.6 + 0.4 * qp}) rotate(${(1 - qp) * 20}deg)`}}>?</div>
        <Kinetic text={text} size={text.length > 24 ? 110 : 130} stagger={3} accent={['KIM', 'SAVOL', 'ODDIY.']} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Chapter: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {n, title, bgFile} = shot.props;
  const p = pop(f, 0, 12, 120);
  const line = ease(f, 6, 22);
  const t = ease(f, 4, 18);
  const glitch = f < 8 ? (f % 2 ? 14 : -14) : 0;
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.6} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -90}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 300, color: 'transparent', WebkitTextStroke: `6px ${C.gold}`, opacity: 0.9 * p, transform: `scale(${1.4 - 0.4 * p}) translateX(${glitch}px)`, lineHeight: 0.9}}>
          {String(n).padStart(2, '0')}
        </div>
        <div style={{width: 900 * line, height: 6, background: C.gold, margin: '26px 0', borderRadius: 3}} />
        <div style={{overflow: 'hidden'}}>
          <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: title.length > 12 ? 92 : 120, color: '#fff', transform: `translateY(${(1 - t) * 110}%)`, letterSpacing: 2, textAlign: 'center', textShadow: '0 10px 40px rgba(0,0,0,0.6)'}}>
            {title}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Checks: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times, center, bgFile} = shot.props;
  const cp = pop(f, 0, 12, 140);
  const pos = [
    [960, 140],
    [470, 640],
    [1450, 640],
  ];
  const cx = 960, cy = 420;
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.62} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {items.map((_: string, i: number) => {
          const at = rel(shot, times[i]);
          const p = ease(f, at, at + 10);
          const [x, y] = pos[i];
          const ex = x + (cx - x) * 0.62 * p, ey = y + (cy - y) * 0.62 * p;
          return (
            <g key={i} opacity={p}>
              <line x1={x} y1={y} x2={ex} y2={ey} stroke={C.cyan} strokeWidth={8} strokeLinecap="round" />
              <circle cx={ex} cy={ey} r={14} fill={C.cyan} />
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: cx, top: cy, transform: `translate(-50%,-50%) scale(${cp})`}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 64, color: '#000', background: C.gold, padding: '22px 40px', borderRadius: 18, boxShadow: `0 0 60px ${C.gold}88`}}>{center}</div>
      </div>
      {items.map((it: string, i: number) => {
        const at = rel(shot, times[i]) - 2;
        const p = pop(f, at, 11, 170);
        const [x, y] = pos[i];
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%,-50%)'}}>
            <Chip text={it} p={p} color={C.cyan} size={i === 0 ? 50 : 40} />
          </div>
        );
      })}
      <div style={{position: 'absolute', top: 760, left: 0, right: 0, textAlign: 'center', fontFamily: BODY, fontWeight: 700, fontSize: 34, color: C.cyan, letterSpacing: 4, opacity: ease(f, sec(2.4), sec(2.8))}}>
        HOKIMIYATNI CHEKLAYDI
      </div>
    </AbsoluteFill>
  );
};

const Rate: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {title, bgFile} = shot.props;
  const pts = [0.62, 0.6, 0.58, 0.6, 0.55, 0.5, 0.46, 0.38, 0.3, 0.2, 0.12];
  const W = 1300, H = 400, x0 = 310, y0 = 170;
  const prog = ease(f, 4, 40, 0, 1, Easing.inOut(Easing.cubic));
  const n = pts.length - 1;
  const upto = prog * n;
  let d = '';
  for (let i = 0; i <= Math.floor(upto); i++) d += `${i ? 'L' : 'M'}${x0 + (i / n) * W},${y0 + pts[i] * H} `;
  const fi = Math.min(n - 1, Math.floor(upto));
  const fr = upto - fi;
  const hx = x0 + ((fi + fr) / n) * W, hy = y0 + (pts[fi] + (pts[fi + 1] - pts[fi]) * fr) * H;
  d += `L${hx},${hy}`;
  const ap = pop(f, 36, 10, 160);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.72} />
      <Title text="AQSH FEDERAL REZERV" top={50} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {[0, 1, 2, 3, 4].map((i) => (
          <line key={i} x1={x0} x2={x0 + W} y1={y0 + (i * H) / 4} y2={y0 + (i * H) / 4} stroke="rgba(255,255,255,0.12)" strokeWidth={2} />
        ))}
        <path d={d} fill="none" stroke={C.red} strokeWidth={12} strokeLinejoin="round" strokeLinecap="round" style={{filter: `drop-shadow(0 0 14px ${C.red})`}} />
        <circle cx={hx} cy={hy} r={18} fill="#fff" />
        <circle cx={hx} cy={hy} r={18 + (f % 20) * 2} fill="none" stroke="#fff" strokeWidth={3} opacity={1 - (f % 20) / 20} />
      </svg>
      <div style={{position: 'absolute', top: 640, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20, transform: `scale(${0.5 + 0.5 * ap})`, opacity: ap}}>
        <svg width={90} height={90} viewBox="0 0 100 100"><path d="M50 5 L95 60 H65 V95 H35 V60 H5 Z" fill={C.red} /></svg>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 84, color: '#fff'}}>{title}</div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- globe ----------
const land = feature(world as any, (world as any).objects.countries) as any;
const DC: [number, number] = [-77.04, 38.9];
const TAS: [number, number] = [69.24, 41.3];
const MapG: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {to, caption} = shot.props;
  const len = sec(shot.dur);
  const rotP = to ? ease(f, 6, Math.min(len - 6, 60), 0, 1, Easing.inOut(Easing.cubic)) : 0;
  const lon = to ? DC[0] + (TAS[0] - DC[0]) * rotP : DC[0] + f * 0.15;
  const lat = to ? 25 + 10 * Math.sin(rotP * Math.PI) : 25;
  const R = 360;
  const proj = useMemo(() => geoOrthographic().scale(R).translate([960, 450]).clipAngle(90), []);
  proj.rotate([-lon, -lat * 0.6]);
  const path = geoPath(proj);
  const grat = geoGraticule10();
  const arcP = to ? ease(f, 10, Math.min(len - 4, 66)) : 0;
  const interp = geoInterpolate(DC, TAS);
  const arcPts: [number, number][] = [];
  for (let i = 0; i <= 60 * arcP; i++) arcPts.push(interp(i / 60));
  const arc = arcPts.length > 1 ? path({type: 'LineString', coordinates: arcPts} as any) : null;
  const pin = (c: [number, number], label: string, color: string, delay: number) => {
    const xy = proj(c);
    const visible = path({type: 'Point', coordinates: c} as any);
    if (!xy || !visible) return null;
    const p = pop(f, delay, 10, 150);
    return (
      <g transform={`translate(${xy[0]},${xy[1]})`} opacity={p}>
        <circle r={14 + (f % 30)} fill="none" stroke={color} strokeWidth={3} opacity={1 - (f % 30) / 30} />
        <circle r={14} fill={color} />
        <text y={-32} textAnchor="middle" fill="#fff" style={{fontFamily: HEAD, fontWeight: 900, fontSize: 40, paintOrder: 'stroke', stroke: '#000', strokeWidth: 8}}>
          {label}
        </text>
      </g>
    );
  };
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        <defs>
          <radialGradient id="ocean" cx="40%" cy="35%">
            <stop offset="0%" stopColor="#1d3a6b" />
            <stop offset="100%" stopColor="#081428" />
          </radialGradient>
        </defs>
        <circle cx={960} cy={450} r={R + 30} fill="none" stroke="rgba(61,220,255,0.15)" strokeWidth={30} />
        <circle cx={960} cy={450} r={R} fill="url(#ocean)" />
        <path d={path(grat) || ''} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={1.5} />
        {land.features.map((ft: any, i: number) => {
          const id = String(ft.id);
          const hi = id === '840' || (to && id === '860');
          return <path key={i} d={path(ft) || ''} fill={hi ? (id === '860' ? C.gold : C.cyan) : '#2b3b55'} stroke="#0b1424" strokeWidth={1} />;
        })}
        {!to
          ? [0, 1, 2].map((k) => {
              const xy = proj(DC);
              const r = ((f + k * 25) % 75) * 7;
              return xy ? <circle key={k} cx={xy[0]} cy={xy[1]} r={r} fill="none" stroke={C.red} strokeWidth={4} opacity={1 - r / 525} /> : null;
            })
          : null}
        {arc ? <path d={arc} fill="none" stroke={C.gold} strokeWidth={8} strokeLinecap="round" style={{filter: `drop-shadow(0 0 10px ${C.gold})`}} /> : null}
        {pin(DC, 'WASHINGTON', C.cyan, 2)}
        {to ? pin(TAS, to, C.gold, Math.min(len - 10, 50)) : null}
      </svg>
      <div style={{position: 'absolute', top: 400, left: 90}}>
        <Chip text={caption} p={pop(f, 8, 12, 150)} size={52} style={{display: 'inline-block'}} />
      </div>
    </AbsoluteFill>
  );
};

const Fx: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {title, sub, bgFile} = shot.props;
  const W = 1300, x0 = 310, y0 = 200, H = 340;
  const N = 60;
  const pts: string[] = [];
  const prog = ease(f, 0, 50);
  for (let i = 0; i <= N * prog; i++) {
    const x = x0 + (i / N) * W;
    const y = y0 + H * (0.6 - 0.35 * (i / N) + 0.12 * Math.sin(i * 0.7) + 0.06 * Math.sin(i * 2.3));
    pts.push(`${i ? 'L' : 'M'}${x},${y}`);
  }
  const sp = pop(f, sec(1.8), 10, 160);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.72} />
      <Title text={title} top={50} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        <path d={pts.join(' ')} fill="none" stroke={C.green} strokeWidth={8} style={{filter: `drop-shadow(0 0 10px ${C.green})`}} />
        <text x={x0} y={y0 - 40} fill="#fff" style={{fontFamily: HEAD, fontWeight: 900, fontSize: 64}}>USD</text>
      </svg>
      <div style={{position: 'absolute', top: 650, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
        <Chip text={`${sub} ▲`} p={sp} color={C.red} size={60} />
      </div>
    </AbsoluteFill>
  );
};

const Link: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {a, aSub, b, bSub} = shot.props;
  const A = [430, 430], B = [1490, 430];
  const lp = ease(f, 10, 40);
  const dot = (f % 40) / 40;
  const bez = (t: number) => {
    const cx = 960, cy = 80;
    const x = (1 - t) ** 2 * A[0] + 2 * (1 - t) * t * cx + t * t * B[0];
    const y = (1 - t) ** 2 * A[1] + 2 * (1 - t) * t * cy + t * t * B[1];
    return [x, y];
  };
  const dp = bez(dot * lp);
  const node = (xy: number[], t1: string, t2: string, color: string, d: number) => {
    const p = pop(f, d, 11, 150);
    return (
      <div style={{position: 'absolute', left: xy[0], top: xy[1], transform: `translate(-50%,-50%) scale(${p})`, textAlign: 'center'}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 76, color: '#000', background: color, padding: '14px 40px', borderRadius: 18}}>{t1}</div>
        <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 38, color: '#fff', marginTop: 14, textTransform: 'uppercase', letterSpacing: 2}}>{t2}</div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <BG dark={0.1} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        <path d={`M${A[0]},${A[1]} Q960,80 ${B[0]},${B[1]}`} fill="none" stroke="rgba(255,255,255,0.8)" strokeWidth={6} strokeDasharray="14 14" strokeDashoffset={-f * 2} pathLength={1000} style={{clipPath: `inset(0 0 ${(1 - lp) * 100}% 0)`}} />
        {lp > 0.95 ? <circle cx={dp[0]} cy={dp[1]} r={16} fill={C.gold} style={{filter: `drop-shadow(0 0 12px ${C.gold})`}} /> : null}
      </svg>
      {node(A, a, aSub, C.cyan, 0)}
      {node(B, b, bSub, C.gold, 22)}
      <div style={{position: 'absolute', top: 400, left: 0, right: 0, textAlign: 'center', fontFamily: HEAD, fontWeight: 800, fontSize: 36, color: C.dim, letterSpacing: 3, opacity: ease(f, 30, 44)}}>BILVOSITA TA'SIR</div>
    </AbsoluteFill>
  );
};

const Names: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times, bgFile} = shot.props;
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.66} />
      <Title text="ENG YIRIK INVESTITSIYA KOMPANIYALARI" top={60} />
      <AbsoluteFill style={{justifyContent: 'flex-start', paddingTop: 190, paddingLeft: 520, gap: 40}}>
        {items.map((it: string, i: number) => {
          const at = rel(shot, times[i]) - 3;
          const p = pop(f, at, 12, 160);
          const w = ease(f, at, at + 10);
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, opacity: Math.min(1, p * 1.5), transform: `translateX(${(1 - p) * -200}px)`}}>
              <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 60, color: C.gold, width: 90}}>0{i + 1}</div>
              <div style={{position: 'relative'}}>
                <div style={{position: 'absolute', inset: '8px -14px', background: 'rgba(255,255,255,0.1)', transform: `scaleX(${w})`, transformOrigin: 'left', borderLeft: `8px solid ${C.gold}`}} />
                <div style={{position: 'relative', fontFamily: HEAD, fontWeight: 900, fontSize: 100, color: '#fff', letterSpacing: -2}}>{it}</div>
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Counter: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {title, bgFile} = shot.props;
  const p = ease(f, 0, sec(Math.min(2.6, shot.dur - 0.4)), 0, 1, Easing.out(Easing.exp));
  const v = p > 0.995 ? 1e12 : Math.floor(1e12 * p);
  const s = v.toLocaleString('en-US').replace(/,/g, ' ');
  const tp = pop(f, sec(1.2), 11, 150);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.7} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -110}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 140, color: C.green, letterSpacing: -2, textShadow: `0 0 40px ${C.green}88`, fontVariantNumeric: 'tabular-nums'}}>
          ${s}
          {p > 0.995 ? '+' : ''}
        </div>
        <div style={{marginTop: 30, transform: `scale(${tp})`, fontFamily: HEAD, fontWeight: 900, fontSize: 80, color: '#fff', background: 'rgba(0,0,0,0.5)', padding: '10px 30px', borderRadius: 14}}>{title}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Grid: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, clipFiles, times, title} = shot.props;
  const n = items.length;
  const cols = n;
  const tileW = n === 4 ? 400 : 520;
  const tileH = n === 4 ? 520 : 560;
  const top = n === 4 ? 150 : 150;
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      {title ? <Title text={title} top={50} /> : null}
      <div style={{position: 'absolute', top, left: (1920 - (cols * tileW + (cols - 1) * 30)) / 2, width: cols * tileW + (cols - 1) * 30, display: 'flex', flexWrap: 'wrap', gap: 30}}>
        {items.map((it: string, i: number) => {
          const at = rel(shot, times[i]) - 3;
          const p = pop(f, at, 12, 150);
          return (
            <div key={i} style={{position: 'relative', width: tileW, height: tileH, borderRadius: 26, overflow: 'hidden', transform: `scale(${0.5 + 0.5 * p})`, opacity: Math.min(1, p * 1.5), border: `3px solid ${C.gold}`, boxShadow: '0 20px 50px rgba(0,0,0,0.6)'}}>
              {f >= at - 2 ? <OffthreadVideo src={staticFile(clipFiles[i])} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : null}
              <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: '50px 20px 18px', background: 'linear-gradient(transparent, rgba(0,0,0,0.85))', fontFamily: HEAD, fontWeight: 900, fontSize: n === 4 ? 40 : 58, color: '#fff', textAlign: 'center'}}>
                {it}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Vs: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {a, b, clipAFile, clipBFile, times} = shot.props;
  const pa = ease(f, 0, 10);
  const tb = rel(shot, times[1]) - 3;
  const pb = ease(f, tb, tb + 10);
  const vp = pop(f, tb + 4, 9, 200);
  const half = (file: string, txt: string, p: number, topSide: boolean, color: string) => (
    <div style={{position: 'absolute', top: 0, bottom: 0, left: topSide ? 0 : 960, width: 960, overflow: 'hidden', transform: `translateY(${(1 - p) * (topSide ? -1080 : 1080)}px)`}}>
      <OffthreadVideo src={staticFile(file)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      <AbsoluteFill style={{background: 'rgba(0,0,0,0.35)'}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 280, textAlign: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 150, color, ...textStroke(8, '#000'), letterSpacing: 4}}>{txt}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {half(clipAFile, a, pa, true, C.green)}
      {half(clipBFile, b, pb, false, C.cyan)}
      <div style={{position: 'absolute', top: 0, bottom: 0, left: 960 - 4, width: 8, background: '#fff', transform: `scaleY(${pb})`}} />
      <div style={{position: 'absolute', left: 960, top: 400, transform: `translate(-50%,-50%) scale(${vp})`, width: 200, height: 200, borderRadius: 100, background: C.gold, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 56, color: '#000', boxShadow: '0 0 60px rgba(0,0,0,0.7)'}}>
        YOKI?
      </div>
    </AbsoluteFill>
  );
};

const APP_COLORS: Record<string, string[]> = {
  Instagram: ['#f58529', '#dd2a7b', '#8134af'],
  YouTube: ['#ff2a2a', '#c40000', '#7a0000'],
  Google: ['#4285F4', '#34A853', '#FBBC05'],
};
const Phone: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {app, q} = shot.props;
  const cols = APP_COLORS[app] || ['#888', '#666', '#444'];
  const p = pop(f, 0, 13, 120);
  const scroll = f * 6;
  const isG = app === 'Google';
  return (
    <AbsoluteFill>
      <BG dark={0.1} />
      <div style={{position: 'absolute', top: 300, left: 140, width: 640, fontFamily: HEAD, fontWeight: 900, fontSize: 76, color: '#fff', lineHeight: 1.1, opacity: ease(f, 4, 14)}}>
        {q}
      </div>
      <div style={{position: 'absolute', left: 1000, top: 60, width: 440, height: 780, borderRadius: 64, background: '#0d0f14', border: '12px solid #2a2e38', overflow: 'hidden', transform: `translateY(${(1 - p) * 500}px) rotate(${(1 - p) * -8}deg)`, boxShadow: `0 40px 100px rgba(0,0,0,0.7), 0 0 80px ${cols[0]}44`}}>
        <div style={{height: 120, background: `linear-gradient(90deg, ${cols.join(',')})`, display: 'flex', alignItems: 'flex-end', padding: '0 0 18px 30px', fontFamily: HEAD, fontWeight: 900, fontSize: 48, color: '#fff'}}>{app}</div>
        {isG ? (
          <div style={{margin: 24, padding: '18px 24px', borderRadius: 40, background: '#fff', fontFamily: BODY, fontWeight: 700, fontSize: 28, color: '#333'}}>
            {'dunyoni kim boshqaradi'.slice(0, Math.floor(f / 2))}
            <span style={{opacity: f % 20 < 10 ? 1 : 0}}>|</span>
          </div>
        ) : null}
        <div style={{transform: `translateY(${-(scroll % 300)}px)`}}>
          {Array.from({length: 8}).map((_, i) => {
            const rank = isG ? i : -1;
            return (
              <div key={i} style={{margin: '18px 24px', borderRadius: 22, background: '#1a1e27', padding: 18, border: rank === 0 && isG ? `3px solid ${C.gold}` : 'none'}}>
                {isG ? null : <div style={{height: 200, borderRadius: 14, background: `linear-gradient(135deg, ${cols[i % 3]}88, #222)`}} />}
                <div style={{height: 20, width: '80%', borderRadius: 10, background: '#3a4050', marginTop: 14}} />
                <div style={{height: 20, width: '55%', borderRadius: 10, background: '#2e3340', marginTop: 10}} />
              </div>
            );
          })}
        </div>
      </div>
      {/* recommendation pointer */}
      <div style={{position: 'absolute', left: 1480, top: 360, opacity: ease(f, 20, 30), transform: `translateX(${Math.sin(f / 4) * 10}px)`}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 42, color: C.gold}}>◀ ALGORITM</div>
      </div>
    </AbsoluteFill>
  );
};

const Algo: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times, out, bgFile} = shot.props;
  const cx = 960, cy = 420;
  const op = pop(f, sec(shot.dur) - sec(2.2), 11, 150);
  return (
    <AbsoluteFill>
      <BG file={bgFile} dark={0.7} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {items.map((_: string, i: number) => {
          const y = 220 + i * 200;
          const at = rel(shot, times[i]);
          const p = ease(f, at, at + 14);
          return <path key={i} d={`M${560},${y} C ${720} ${y}, ${cx - 300} ${cy}, ${cx - 120} ${cy}`} fill="none" stroke={C.cyan} strokeWidth={4} strokeDasharray="12 10" strokeDashoffset={-f * 2} opacity={p} />;
        })}
        {[0, 1, 2].map((k) => (
          <circle key={k} cx={cx} cy={cy} r={110 + k * 28} fill="none" stroke={k === 0 ? C.gold : 'rgba(255,200,61,0.4)'} strokeWidth={k === 0 ? 6 : 3} strokeDasharray={k === 0 ? 'none' : '20 16'} transform={`rotate(${f * (k % 2 ? -2 : 2)} ${cx} ${cy})`} />
        ))}
        <line x1={cx + 170} y1={cy} x2={cx + 330} y2={cy} stroke={C.gold} strokeWidth={6} opacity={op} />
      </svg>
      {items.map((it: string, i: number) => {
        const at = rel(shot, times[i]) - 3;
        return (
          <div key={i} style={{position: 'absolute', right: 1920 - 580, top: 220 + i * 200, transform: 'translateY(-50%)'}}>
            <Chip text={it} p={pop(f, at, 11, 160)} color={C.cyan} size={38} />
          </div>
        );
      })}
      <div style={{position: 'absolute', left: cx, top: cy, transform: 'translate(-50%,-50%)', fontFamily: HEAD, fontWeight: 900, fontSize: 40, color: C.gold, letterSpacing: 2}}>ALGORITM</div>
      <div style={{position: 'absolute', left: cx + 340, top: cy, transform: 'translateY(-50%)'}}>
        <Chip text={out} p={op} color={C.gold} size={44} />
      </div>
    </AbsoluteFill>
  );
};

const Split3: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, clipFiles, times} = shot.props;
  const H = 1920 / 3; // column width
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {items.map((it: string, i: number) => {
        const at = rel(shot, times[i]) - 3;
        const p = ease(f, at, at + 10);
        return (
          <div key={i} style={{position: 'absolute', top: 0, bottom: 0, left: i * H, width: H - 6, overflow: 'hidden', clipPath: `inset(0 0 ${(1 - p) * 100}% 0)`}}>
            {f >= at - 2 ? <OffthreadVideo src={staticFile(clipFiles[i])} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : null}
            <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.7), rgba(0,0,0,0.05) 50%)'}} />
            <div style={{position: 'absolute', left: 50, top: 150, fontFamily: HEAD, fontWeight: 900, fontSize: 30, color: C.gold, letterSpacing: 4}}>{i + 1}-INSON</div>
            <div style={{position: 'absolute', left: 50, top: 190, fontFamily: HEAD, fontWeight: 900, fontSize: 72, color: '#fff', ...textStroke(4, 'rgba(0,0,0,0.6)')}}>{it}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const NODES = [
  {t: 'AQSH', x: 960, y: 170},
  {t: 'XITOY', x: 1470, y: 280},
  {t: 'ROSSIYA', x: 1500, y: 640},
  {t: 'YEVROPA', x: 960, y: 760},
  {t: 'BANKLAR', x: 420, y: 640},
  {t: 'KOMPANIYALAR', x: 450, y: 280},
  {t: 'ODDIY INSONLAR', x: 960, y: 465},
];
const Network: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {step} = shot.props;
  if (step === 0) {
    const p = pop(f, 0, 12, 140);
    const x = ease(f, 18, 30);
    return (
      <AbsoluteFill>
        <BG dark={0.2} />
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -100}}>
          <div style={{position: 'relative', transform: `scale(${p})`}}>
            <div style={{width: 300, height: 300, borderRadius: 150, border: `6px solid ${C.gold}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 44, color: '#fff', textAlign: 'center', background: 'rgba(255,200,61,0.1)'}}>
              BITTA
              <br />
              MARKAZ
            </div>
            <svg width={360} height={360} style={{position: 'absolute', left: -30, top: -30}}>
              <line x1={30} y1={30} x2={30 + 300 * x} y2={30 + 300 * x} stroke={C.red} strokeWidth={16} strokeLinecap="round" />
              <line x1={330} y1={30} x2={330 - 300 * x} y2={30 + 300 * x} stroke={C.red} strokeWidth={16} strokeLinecap="round" />
            </svg>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  const edges: [number, number][] = [];
  for (let i = 0; i < NODES.length; i++) for (let j = i + 1; j < NODES.length; j++) edges.push([i, j]);
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {edges.map(([i, j], k) => {
          const p = step === 2 ? ease(f, k, k + 12) : ease(f, 10 + k, 22 + k) * 0.35;
          const a = NODES[i], b = NODES[j];
          return (
            <line key={k} x1={a.x} y1={a.y} x2={a.x + (b.x - a.x) * p} y2={a.y + (b.y - a.y) * p} stroke={step === 2 ? C.gold : 'rgba(255,255,255,0.5)'} strokeWidth={step === 2 ? 3 : 2} opacity={step === 2 ? 0.55 + 0.3 * Math.sin((f + k * 5) / 8) : 0.6} />
          );
        })}
      </svg>
      {NODES.map((n, i) => {
        const p = pop(f, step === 2 ? 0 : i * 3, 11, 160);
        return (
          <div key={i} style={{position: 'absolute', left: n.x, top: n.y, transform: 'translate(-50%,-50%)'}}>
            <Chip text={n.t} p={p} size={n.t.length > 10 ? 30 : 38} color={i === 6 ? C.green : C.gold} />
          </div>
        );
      })}
      <div style={{position: 'absolute', top: 50, left: 0, right: 0, textAlign: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 44, color: '#fff', opacity: ease(f, 6, 18)}}>
        {step === 2 ? 'HAMMASI BOG\'LANGAN' : 'RAQOBATLASHAYOTGAN KUCHLAR'}
      </div>
    </AbsoluteFill>
  );
};

const CENTERS = ['DAVLATLAR', 'MARKAZIY BANKLAR', 'KORPORATSIYALAR', 'AXBOROT PLATFORMALARI', 'XALQARO TASHKILOTLAR'];
const Centers: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {step} = shot.props;
  const cx = 960, cy = 460, R = 600, RY = 310;
  const sp = step === 0 ? ease(f, 6, 30, 0, 1, Easing.out(Easing.back(1.4))) : 1;
  const dim = step === 1 ? ease(f, sec(1.2), sec(1.8)) : 0;
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <div style={{position: 'absolute', top: 40, left: 0, right: 0, textAlign: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 48, color: '#fff', opacity: ease(f, 2, 14)}}>
        {step === 0 ? 'HOKIMIYAT BO\'LINGAN' : 'HECH BIRI MUTLAQ EMAS'}
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {CENTERS.map((_, i) => {
          const a = -Math.PI / 2 + (i / 5) * Math.PI * 2;
          const x = cx + Math.cos(a) * R * sp, y = cy + Math.sin(a) * RY * sp;
          return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={step === 1 ? C.red : C.gold} strokeWidth={4} strokeDasharray="10 10" strokeDashoffset={-f} opacity={0.7} />;
        })}
      </svg>
      <div style={{position: 'absolute', left: cx, top: cy, transform: `translate(-50%,-50%) scale(${1 - 0.3 * sp})`, width: 220, height: 220, borderRadius: 110, background: step === 1 ? 'rgba(255,61,61,0.2)' : 'rgba(255,200,61,0.2)', border: `5px solid ${step === 1 ? C.red : C.gold}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD, fontWeight: 900, fontSize: 34, color: '#fff'}}>
        HOKIMIYAT
      </div>
      {CENTERS.map((t, i) => {
        const a = -Math.PI / 2 + (i / 5) * Math.PI * 2;
        const x = cx + Math.cos(a) * R * sp, y = cy + Math.sin(a) * RY * sp;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%,-50%)', opacity: 1 - dim * 0.45}}>
            <Chip text={t.replace(' ', '\n')} p={Math.min(1, sp * 1.2)} size={30} style={{whiteSpace: 'pre', textAlign: 'center'}} color={step === 1 ? C.red : C.gold} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Neq: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {a, b} = shot.props;
  const pa = pop(f, 0, 12, 150);
  const pn = pop(f, 10, 9, 200);
  const pb = pop(f, 18, 12, 150);
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -110, gap: 0}}>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 92, color: C.cyan, transform: `scale(${pa})`, textAlign: 'center', width: 1600}}>{a}</div>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 200, color: C.red, lineHeight: 1, transform: `scale(${pn}) rotate(${(1 - pn) * 90}deg)`}}>≠</div>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 92, color: C.gold, transform: `scale(${pb})`, textAlign: 'center', width: 1600}}>{b}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Strike: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {text} = shot.props;
  const s = ease(f, sec(shot.dur * 0.55), sec(shot.dur * 0.55) + 10);
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -110}}>
        <div style={{position: 'relative', opacity: 1 - s * 0.35}}>
          <Kinetic text={text} size={104} stagger={3} />
          <div style={{position: 'absolute', left: -20, right: -20, top: '50%', height: 16, background: C.red, transform: `scaleX(${s}) rotate(-4deg)`, transformOrigin: 'left', borderRadius: 8}} />
        </div>
        <div style={{marginTop: 40, fontFamily: HEAD, fontWeight: 900, fontSize: 70, color: C.red, opacity: s}}>ENG MUHIM SAVOL EMAS</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Triad: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times} = shot.props;
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <Title text="ENG MUHIM SAVOL" top={60} />
      <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: 190, gap: 34}}>
        {items.map((it: string, i: number) => {
          const at = rel(shot, times[i]) - 3;
          const p = pop(f, at, 12, 160);
          return (
            <div key={i} style={{fontFamily: HEAD, fontWeight: 900, fontSize: it.length > 16 ? 76 : 96, color: i === 2 ? C.gold : '#fff', transform: `translateY(${(1 - p) * 80}px) scale(${0.7 + 0.3 * p})`, opacity: Math.min(1, p * 1.5), textAlign: 'center', ...textStroke(4, 'rgba(0,0,0,0.5)')}}>
              {it}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Poll: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {items, times} = shot.props;
  let active = -1;
  times.forEach((t: number, i: number) => {
    if (f >= rel(shot, t) - 3) active = i;
  });
  const hp = pop(f, 0, 12, 140);
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <div style={{position: 'absolute', top: 50, left: 60, right: 60, textAlign: 'center', transform: `scale(${hp})`}}>
        <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 34, color: C.gold, letterSpacing: 4}}>SIZNINGCHA</div>
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 72, color: '#fff', lineHeight: 1.1, marginTop: 10}}>ENG KATTA KUCH KIMDA?</div>
      </div>
      <div style={{position: 'absolute', top: 250, left: 460, right: 460, display: 'flex', flexDirection: 'column', gap: 20}}>
        {items.map((it: string, i: number) => {
          const at = sec(0.6) + i * 4;
          const p = pop(f, at, 12, 160);
          const on = i === active;
          return (
            <div key={i} style={{position: 'relative', height: 108, borderRadius: 54, border: `4px solid ${on ? C.gold : 'rgba(255,255,255,0.35)'}`, background: on ? 'rgba(255,200,61,0.18)' : 'rgba(10,14,24,0.6)', display: 'flex', alignItems: 'center', padding: '0 40px', gap: 26, transform: `translateX(${(1 - p) * 600}px) scale(${on ? 1.04 : 1})`, opacity: Math.min(1, p * 1.5)}}>
              <div style={{width: 54, height: 54, borderRadius: 27, border: `4px solid ${on ? C.gold : '#fff'}`, background: on ? C.gold : 'transparent'}} />
              <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: it.length > 16 ? 40 : 50, color: '#fff'}}>{it}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Cta: React.FC<P> = ({shot}) => {
  const f = useCurrentFrame();
  const {text} = shot.props;
  const p = pop(f, 0, 12, 140);
  const typed = text.slice(0, Math.floor(f * 1.2));
  return (
    <AbsoluteFill>
      <BG dark={0.2} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -110}}>
        <svg width={170} height={150} viewBox="0 0 100 90" style={{transform: `scale(${p}) rotate(${Math.sin(f / 6) * 6}deg)`}}><path d="M10 5 H90 Q95 5 95 10 V58 Q95 63 90 63 H40 L20 82 V63 H10 Q5 63 5 58 V10 Q5 5 10 5 Z" fill={C.gold} /><circle cx={30} cy={34} r={6} fill="#000" /><circle cx={50} cy={34} r={6} fill="#000" /><circle cx={70} cy={34} r={6} fill="#000" /></svg>
        <div style={{marginTop: 24, width: 1000, borderRadius: 30, background: 'rgba(255,255,255,0.95)', padding: '30px 36px', transform: `scale(${p})`, boxShadow: '0 30px 80px rgba(0,0,0,0.5)'}}>
          <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 30, color: '#888'}}>Izoh qoldiring...</div>
          <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: 48, color: '#111', marginTop: 8}}>
            {typed}
            <span style={{opacity: f % 20 < 10 ? 1 : 0, color: C.red}}>|</span>
          </div>
        </div>
        <svg width={110} height={110} viewBox="0 0 100 100" style={{marginTop: 40, transform: `translateY(${Math.abs(Math.sin(f / 5)) * 24}px)`}}><path d="M35 5 H65 V55 H90 L50 95 L10 55 H35 Z" fill="#fff" /></svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const MG: React.FC<P> = (props) => {
  switch (props.shot.mg) {
    case 'who': return <Who {...props} />;
    case 'factors': return <Factors {...props} />;
    case 'question': return <Question {...props} />;
    case 'chapter': return <Chapter {...props} />;
    case 'checks': return <Checks {...props} />;
    case 'rate': return <Rate {...props} />;
    case 'map': return <MapG {...props} />;
    case 'fx': return <Fx {...props} />;
    case 'link': return <Link {...props} />;
    case 'names': return <Names {...props} />;
    case 'counter': return <Counter {...props} />;
    case 'grid': return <Grid {...props} />;
    case 'vs': return <Vs {...props} />;
    case 'phone': return <Phone {...props} />;
    case 'algo': return <Algo {...props} />;
    case 'split3': return <Split3 {...props} />;
    case 'network': return <Network {...props} />;
    case 'centers': return <Centers {...props} />;
    case 'neq': return <Neq {...props} />;
    case 'strike': return <Strike {...props} />;
    case 'triad': return <Triad {...props} />;
    case 'poll': return <Poll {...props} />;
    case 'cta': return <Cta {...props} />;
    default: return <BG />;
  }
};
