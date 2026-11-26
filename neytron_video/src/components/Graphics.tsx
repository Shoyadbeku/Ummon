import React, {useMemo} from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {geoMercator, geoPath, geoGraticule10} from 'd3-geo';
import {feature} from 'topojson-client';
// Natural Earth 1:50m (public domain), packaged by world-atlas.
import world from 'world-atlas/countries-50m.json';
import {C, condensed, sans, serif} from '../theme';
import {Pin} from '../data/types';
import {useMove} from './Media';

const ease = Easing.bezier(0.25, 0.1, 0.25, 1);

const Backdrop: React.FC<{tone?: 'red' | 'dark'}> = ({tone = 'dark'}) => {
  const frame = useCurrentFrame();
  const drift = frame * 0.15;
  return (
    <AbsoluteFill
      style={{
        background:
          tone === 'red'
            ? `radial-gradient(circle at ${40 + Math.sin(drift / 40) * 6}% 40%, #3a0a0d 0%, #12070a 55%, #050506 100%)`
            : `radial-gradient(circle at ${50 + Math.sin(drift / 50) * 8}% 35%, #1b2029 0%, #0b0d12 55%, #040506 100%)`,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          backgroundPosition: `${drift}px ${drift * 0.5}px`,
        }}
      />
    </AbsoluteFill>
  );
};

const useIn = (delay = 0, dur = 20) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: {damping: 200}, durationInFrames: dur});
};

const useOut = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};

/** Words revealed one by one (kinetic typography). */
const Stagger: React.FC<{text: string; delay?: number; style: React.CSSProperties}> = ({text, delay = 0, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={style}>
      {text.split(' ').map((w, i) => {
        const p = spring({frame: frame - delay - i * 3, fps, config: {damping: 200}, durationInFrames: 16});
        return (
          <span key={i} style={{display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 30}px)`, filter: `blur(${(1 - p) * 8}px)`, marginRight: '0.28em'}}>
            {w}
          </span>
        );
      })}
    </div>
  );
};

export const Card: React.FC<{kicker?: string; title: string; sub?: string; tone?: 'red' | 'dark'}> = ({kicker, title, sub, tone}) => {
  const k = useIn(2);
  const line = useIn(8, 26);
  const out = useOut();
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 300], [1, 1.04]);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop tone={tone} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', transform: `scale(${scale})`}}>
        {kicker && (
          <div style={{fontFamily: condensed, fontSize: 30, letterSpacing: 10, color: C.red, opacity: k, marginBottom: 18, textTransform: 'uppercase'}}>{kicker}</div>
        )}
        <Stagger
          text={title}
          delay={6}
          style={{fontFamily: serif, fontWeight: 900, fontSize: title.length > 40 ? 76 : 104, color: C.ink, textAlign: 'center', maxWidth: 1500, lineHeight: 1.08}}
        />
        <div style={{height: 3, width: 360 * line, background: C.red, margin: '34px 0 26px'}} />
        {sub && <Stagger text={sub} delay={18} style={{fontFamily: sans, fontSize: 34, color: C.dim, textAlign: 'center', maxWidth: 1300}} />}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const DateCard: React.FC<{date: string; place?: string}> = ({date, place}) => {
  const frame = useCurrentFrame();
  const out = useOut();
  const p = useIn(4, 24);
  const shown = Math.floor(interpolate(frame, [4, 4 + date.length * 2], [0, date.length], {extrapolateRight: 'clamp'}));
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <AbsoluteFill style={{justifyContent: 'center', paddingLeft: 180}}>
        <div style={{fontFamily: condensed, fontWeight: 700, fontSize: 132, color: C.ink, letterSpacing: 4}}>
          {date.slice(0, shown)}
          <span style={{opacity: frame % 20 < 10 ? 1 : 0, color: C.red}}>▍</span>
        </div>
        {place && (
          <div style={{display: 'flex', alignItems: 'center', gap: 20, opacity: p, transform: `translateX(${(1 - p) * -40}px)`}}>
            <div style={{width: 60, height: 4, background: C.red}} />
            <div style={{fontFamily: sans, fontSize: 44, color: C.dim, letterSpacing: 3, textTransform: 'uppercase'}}>{place}</div>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Question: React.FC<{lines: string[]}> = ({lines}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const out = useOut();
  const per = Math.max(10, Math.floor((durationInFrames - 20) / lines.length));
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop tone="red" />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 22}}>
        {lines.map((l, i) => {
          const p = spring({frame: frame - i * per, fps: 30, config: {damping: 200}, durationInFrames: 18});
          const active = frame >= i * per && (i === lines.length - 1 || frame < (i + 1) * per);
          return (
            <div
              key={i}
              style={{
                fontFamily: serif,
                fontWeight: 700,
                fontSize: 66,
                color: active ? C.ink : 'rgba(244,241,234,0.35)',
                opacity: p,
                transform: `translateY(${(1 - p) * 30}px)`,
                textAlign: 'center',
                maxWidth: 1500,
              }}
            >
              {l}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Stat: React.FC<{value: number; prefix?: string; suffix?: string; label: string; decimals?: number}> = ({value, prefix = '', suffix = '', label, decimals = 0}) => {
  const frame = useCurrentFrame();
  const out = useOut();
  const t = interpolate(frame, [6, 50], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const p = useIn(30);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <div style={{fontFamily: condensed, fontWeight: 700, fontSize: 230, color: C.ink, lineHeight: 1}}>
          {prefix}
          {(value * t).toFixed(decimals)}
          <span style={{color: C.red}}>{suffix}</span>
        </div>
        <div style={{fontFamily: sans, fontSize: 40, color: C.dim, opacity: p, marginTop: 20, textAlign: 'center', maxWidth: 1300}}>{label}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Timeline: React.FC<{items: {year: string; label: string}[]; active: number}> = ({items, active}) => {
  const frame = useCurrentFrame();
  const out = useOut();
  const w = 1500;
  const step = w / Math.max(1, items.length - 1);
  const prog = interpolate(frame, [0, 30], [Math.max(0, active - 1), active], {extrapolateRight: 'clamp', easing: ease});
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <div style={{position: 'absolute', left: 210, top: 540, width: w, height: 4, background: 'rgba(255,255,255,0.18)'}} />
      <div style={{position: 'absolute', left: 210, top: 540, width: step * prog, height: 4, background: C.red}} />
      {items.map((it, i) => {
        const on = i <= active;
        const cur = i === active;
        const p = spring({frame: frame - i * 3, fps: 30, config: {damping: 200}, durationInFrames: 16});
        return (
          <div key={i} style={{position: 'absolute', left: 210 + i * step - 120, top: 470, width: 240, textAlign: 'center', opacity: p}}>
            <div style={{fontFamily: condensed, fontSize: cur ? 54 : 38, fontWeight: 700, color: cur ? C.ink : on ? C.dim : 'rgba(255,255,255,0.3)', height: 60}}>{it.year}</div>
            <div
              style={{
                width: cur ? 26 : 16,
                height: cur ? 26 : 16,
                borderRadius: '50%',
                margin: `${cur ? 0 : 5}px auto`,
                background: on ? C.red : '#333',
                boxShadow: cur ? `0 0 30px ${C.red}` : 'none',
              }}
            />
            <div style={{fontFamily: sans, fontSize: cur ? 28 : 22, color: cur ? C.ink : 'rgba(255,255,255,0.45)', marginTop: 18, lineHeight: 1.25}}>{it.label}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Kim family tree. Photos are only used for people with verified, licensed portraits. */
const TREE: {id: string; name: string; years: string; x: number; y: number; photo?: string; parent?: string}[] = [
  {id: 'ilsung', name: 'Kim Ir Sen', years: '1912–1994', x: 960, y: 130, photo: 'media/kim_il_sung.jpg'},
  {id: 'jongil', name: 'Kim Chen Ir', years: '1941–2011', x: 960, y: 390, photo: 'media/kim_jong_il.jpg', parent: 'ilsung'},
  {id: 'jongnam', name: 'Kim Chen Nam', years: '1971–2017', x: 420, y: 665, parent: 'jongil'},
  {id: 'jongchol', name: 'Kim Chen Chol', years: '1981–', x: 780, y: 665, parent: 'jongil'},
  {id: 'jongun', name: 'Kim Chen In', years: '1984–', x: 1140, y: 665, photo: 'media/kim_jong_un_portrait.jpg', parent: 'jongil'},
  {id: 'yojong', name: 'Kim Yo Jong', years: '1987/88–', x: 1500, y: 665, photo: 'media/kim_yo_jong.jpg', parent: 'jongil'},
];

export const FamilyTree: React.FC<{focus: string[]; dead?: string[]}> = ({focus, dead = []}) => {
  const frame = useCurrentFrame();
  const out = useOut();
  const byId = Object.fromEntries(TREE.map((n) => [n.id, n]));
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {TREE.filter((n) => n.parent).map((n, i) => {
          const p = byId[n.parent!];
          const d = `M${p.x},${p.y + 128} C${p.x},${(p.y + n.y) / 2 + 60} ${n.x},${(p.y + n.y) / 2 - 10} ${n.x},${n.y - 118}`;
          const prog = interpolate(frame, [4 + i * 4, 30 + i * 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const hl = focus.includes(n.id) && focus.includes(p.id);
          return <path key={n.id} d={d} fill="none" stroke={hl ? C.red : 'rgba(255,255,255,0.25)'} strokeWidth={hl ? 4 : 2} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - prog} />;
        })}
      </svg>
      {TREE.map((n, i) => {
        const p = spring({frame: frame - i * 4, fps: 30, config: {damping: 200}, durationInFrames: 18});
        const f = focus.includes(n.id);
        const isDead = dead.includes(n.id);
        const size = f ? 170 : 130;
        return (
          <div key={n.id} style={{position: 'absolute', left: n.x - 160, top: n.y - size / 2 - 20, width: 320, textAlign: 'center', opacity: p * (f || focus.length === 0 ? 1 : 0.4), transform: `scale(${0.85 + 0.15 * p})`}}>
            <div
              style={{
                width: size,
                height: size,
                margin: '0 auto',
                borderRadius: '50%',
                overflow: 'hidden',
                border: `4px solid ${f ? C.red : 'rgba(255,255,255,0.3)'}`,
                background: 'linear-gradient(160deg,#2a2f3a,#12151b)',
                boxShadow: f ? `0 0 40px rgba(215,38,47,0.45)` : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                filter: isDead ? 'grayscale(1)' : 'none',
              }}
            >
              {n.photo ? (
                <Img src={staticFile(n.photo)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 25%'}} />
              ) : (
                <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 24 24" fill="rgba(255,255,255,0.35)">
                  <circle cx="12" cy="8" r="4.2" />
                  <path d="M3.5 21c.8-4.6 4.2-7 8.5-7s7.7 2.4 8.5 7z" />
                </svg>
              )}
            </div>
            <div style={{fontFamily: condensed, fontWeight: 600, fontSize: f ? 36 : 30, color: f ? C.ink : C.dim, marginTop: 12, textTransform: 'uppercase', letterSpacing: 1}}>
              {n.name}
            </div>
            <div style={{fontFamily: sans, fontSize: 22, color: isDead ? C.red : 'rgba(255,255,255,0.5)'}}>{n.years}</div>
          </div>
        );
      })}
      <div style={{position: 'absolute', left: 60, top: 50, fontFamily: condensed, fontSize: 28, letterSpacing: 6, color: C.red}}>KIMLAR SULOLASI</div>
    </AbsoluteFill>
  );
};

const countries = feature(world as any, (world as any).objects.countries) as any;

/** Animated map from Natural Earth data. Pins drop in sequence; optional arcs between pins. */
export const MapScene: React.FC<{center: [number, number]; scale0: number; scale1: number; pins: Pin[]; arcs?: [string, string][]; caption?: string}> = ({center, scale0, scale1, pins, arcs = [], caption}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const out = useOut();
  const t = interpolate(frame, [0, durationInFrames], [0, 1], {easing: ease});
  const scale = scale0 + (scale1 - scale0) * t;
  const proj = useMemo(() => geoMercator().center(center).scale(scale).translate([960, 540]), [center, scale]);
  const path = geoPath(proj);
  const highlight = new Set(['Malaysia', 'North Korea', 'Dem. Rep. Korea', 'Korea, Dem. People\'s Rep.']);
  const byName = Object.fromEntries(pins.map((p) => [p.name, p]));
  return (
    <AbsoluteFill style={{opacity: out, background: '#06090d'}}>
      <svg width={1920} height={1080}>
        <path d={path(geoGraticule10()) ?? ''} fill="none" stroke="rgba(255,255,255,0.05)" />
        {countries.features.map((f: any, i: number) => {
          const name = f.properties.name;
          const hl = pins.some((p) => p.main) && highlight.has(name);
          return <path key={i} d={path(f) ?? ''} fill={hl ? 'rgba(215,38,47,0.32)' : '#1a1f27'} stroke={hl ? C.red : 'rgba(255,255,255,0.22)'} strokeWidth={hl ? 1.6 : 0.7} />;
        })}
        {arcs.map(([a, b], i) => {
          const A = proj([byName[a].lon, byName[a].lat])!;
          const B = proj([byName[b].lon, byName[b].lat])!;
          const mx = (A[0] + B[0]) / 2;
          const my = Math.min(A[1], B[1]) - Math.abs(A[0] - B[0]) * 0.25 - 40;
          const prog = interpolate(frame, [15 + i * 10, 55 + i * 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return <path key={i} d={`M${A[0]},${A[1]} Q${mx},${my} ${B[0]},${B[1]}`} fill="none" stroke={C.gold} strokeWidth={3} strokeDasharray="1" pathLength={1} strokeDashoffset={1 - prog} />;
        })}
        {pins.map((p, i) => {
          const xy = proj([p.lon, p.lat]);
          if (!xy) return null;
          const s = spring({frame: frame - 8 - i * 8, fps: 30, config: {damping: 12}, durationInFrames: 30});
          const pulse = (frame % 45) / 45;
          return (
            <g key={p.name} transform={`translate(${xy[0]},${xy[1]})`} opacity={Math.min(1, s)}>
              {p.main && <circle r={14 + pulse * 40} fill="none" stroke={C.red} strokeWidth={2} opacity={1 - pulse} />}
              <circle r={p.main ? 11 : 8} fill={p.main ? C.red : C.gold} stroke="#fff" strokeWidth={2} transform={`scale(${s})`} />
              <text x={18} y={-14} fill={C.ink} fontFamily={condensed} fontSize={p.main ? 40 : 30} fontWeight={600} style={{textShadow: '0 2px 8px #000'}} paintOrder="stroke" stroke="#06090d" strokeWidth={6}>
                {p.name}
              </text>
            </g>
          );
        })}
      </svg>
      {caption && <div style={{position: 'absolute', left: 60, top: 50, fontFamily: condensed, fontSize: 28, letterSpacing: 6, color: C.red}}>{caption}</div>}
      <div style={{position: 'absolute', left: 60, bottom: 34, fontFamily: sans, fontSize: 16, color: 'rgba(255,255,255,0.45)'}}>Xarita: Natural Earth (public domain)</div>
    </AbsoluteFill>
  );
};

/** Two verified photos side by side (comparison). */
export const Split: React.FC<{left: {file: string; name: string; move?: any}; right: {file: string; name: string; move?: any}; mid?: string}> = ({left, right, mid}) => {
  const a = useIn(0, 22);
  const b = useIn(8, 22);
  const out = useOut();
  const tl = useMove(left.move);
  const tr = useMove(right.move);
  const panel = (file: string, name: string, p: number, tf: string, side: 'l' | 'r') => (
    <div style={{position: 'absolute', top: 0, bottom: 0, [side === 'l' ? 'left' : 'right']: 0, width: 954, overflow: 'hidden', opacity: p, transform: `translateX(${(1 - p) * (side === 'l' ? -80 : 80)}px)`}}>
      <Img src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 25%', transform: tf, filter: 'contrast(1.06) saturate(0.9)'}} />
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 360, background: 'linear-gradient(transparent, rgba(0,0,0,0.85))'}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 240, background: 'linear-gradient(rgba(0,0,0,0.75), transparent)'}} />
      <div style={{position: 'absolute', left: 50, top: 60, fontFamily: condensed, fontWeight: 700, fontSize: 56, color: C.ink, textTransform: 'uppercase', textShadow: '0 3px 16px #000'}}>{name}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{background: '#000', opacity: out}}>
      {panel(left.file, left.name, a, tl, 'l')}
      {panel(right.file, right.name, b, tr, 'r')}
      <div style={{position: 'absolute', left: 957, top: 0, bottom: 0, width: 6, background: C.red}} />
      {mid && (
        <div style={{position: 'absolute', left: 960, top: 540, transform: 'translate(-50%,-50%)', background: C.red, color: '#fff', fontFamily: condensed, fontWeight: 700, fontSize: 40, padding: '10px 24px'}}>{mid}</div>
      )}
    </AbsoluteFill>
  );
};

/** VX (C11H26NO2PS) skeletal structure, drawn as original graphic. */
export const Molecule: React.FC = () => {
  const frame = useCurrentFrame();
  const out = useOut();
  const atoms: {x: number; y: number; l: string; c: string}[] = [
    {x: 560, y: 520, l: 'C', c: '#888'}, // CH3-P
    {x: 700, y: 440, l: 'P', c: '#e8913a'},
    {x: 700, y: 290, l: 'O', c: '#e04848'}, // P=O
    {x: 840, y: 520, l: 'S', c: '#e6d140'},
    {x: 980, y: 440, l: 'C', c: '#888'},
    {x: 1120, y: 520, l: 'C', c: '#888'},
    {x: 1260, y: 440, l: 'N', c: '#4a7de0'},
    {x: 600, y: 300, l: '', c: ''},
    {x: 640, y: 600, l: 'O', c: '#e04848'}, // P-O-Et
    {x: 520, y: 690, l: 'C', c: '#888'},
    {x: 400, y: 620, l: 'C', c: '#888'},
    {x: 1400, y: 520, l: 'C', c: '#888'}, // iPr 1
    {x: 1260, y: 290, l: 'C', c: '#888'}, // iPr 2
  ];
  const bonds: [number, number, boolean?][] = [
    [0, 1], [1, 2, true], [1, 3], [3, 4], [4, 5], [5, 6], [1, 8], [8, 9], [9, 10], [6, 11], [6, 12],
  ];
  const rot = interpolate(frame, [0, 300], [-3, 3]);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop tone="red" />
      <svg width={1920} height={1080} style={{transform: `rotate(${rot}deg)`}}>
        {bonds.map(([a, b, dbl], i) => {
          const p = interpolate(frame, [i * 3, i * 3 + 18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const A = atoms[a];
          const B = atoms[b];
          return (
            <g key={i}>
              <line x1={A.x} y1={A.y} x2={A.x + (B.x - A.x) * p} y2={A.y + (B.y - A.y) * p} stroke="rgba(255,255,255,0.7)" strokeWidth={6} />
              {dbl && <line x1={A.x + 14} y1={A.y} x2={A.x + 14 + (B.x - A.x) * p} y2={A.y + (B.y - A.y) * p} stroke="rgba(255,255,255,0.7)" strokeWidth={6} />}
            </g>
          );
        })}
        {atoms.map((a, i) => {
          if (!a.l) return null;
          const s = spring({frame: frame - 10 - i * 2, fps: 30, config: {damping: 14}, durationInFrames: 24});
          return (
            <g key={i} transform={`translate(${a.x},${a.y}) scale(${s})`}>
              <circle r={a.l === 'C' ? 30 : 42} fill={a.c} stroke="#000" strokeWidth={3} />
              <text textAnchor="middle" dy={12} fontFamily={condensed} fontSize={34} fontWeight={700} fill="#111">{a.l}</text>
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', left: 0, right: 0, top: 110, textAlign: 'center', fontFamily: condensed, fontWeight: 700, fontSize: 120, color: C.ink, letterSpacing: 10}}>VX</div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 250, textAlign: 'center', fontFamily: sans, fontSize: 30, color: C.dim}}>C₁₁H₂₆NO₂PS · asab-paralitik zahar</div>
      <div style={{position: 'absolute', left: 60, bottom: 34, fontFamily: sans, fontSize: 16, color: 'rgba(255,255,255,0.45)'}}>Grafik: molekula tuzilishi (illustratsiya)</div>
    </AbsoluteFill>
  );
};

/** Clearly-labelled schematic reconstruction (NOT archive footage). */
export const Reconstruction: React.FC<{title: string; lines: string[]}> = ({title, lines}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const out = useOut();
  const per = Math.max(12, Math.floor((durationInFrames - 20) / Math.max(1, lines.length)));
  const ts = new Date(Date.UTC(2017, 1, 13, 9, 0, 0) + frame * 1000 / 30);
  const clock = ts.toISOString().slice(11, 19);
  return (
    <AbsoluteFill style={{opacity: out}}>
      <Backdrop />
      <svg width={1920} height={1080} style={{position: 'absolute', opacity: 0.55}}>
        {/* schematic terminal floor plan */}
        <rect x={260} y={260} width={1400} height={560} fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth={2} />
        {Array.from({length: 8}).map((_, i) => (
          <rect key={i} x={340 + i * 160} y={300} width={110} height={60} fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.25)" />
        ))}
        <text x={340} y={290} fill="rgba(255,255,255,0.5)" fontFamily={sans} fontSize={20}>RO‘YXATDAN O‘TISH KIOSKLARI</text>
      </svg>
      <div style={{position: 'absolute', left: 60, top: 50, display: 'flex', gap: 18, alignItems: 'center'}}>
        <div style={{background: C.red, color: '#fff', fontFamily: condensed, fontWeight: 700, fontSize: 24, padding: '4px 12px', letterSpacing: 3}}>GRAFIK REKONSTRUKSIYA</div>
        <div style={{fontFamily: condensed, fontSize: 28, letterSpacing: 4, color: C.dim}}>{title}</div>
      </div>
      <div style={{position: 'absolute', right: 60, top: 50, fontFamily: 'monospace', fontSize: 30, color: C.dim}}>~{clock}</div>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 26}}>
        {lines.map((l, i) => {
          const p = spring({frame: frame - i * per, fps: 30, config: {damping: 200}, durationInFrames: 16});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, opacity: p, transform: `translateX(${(1 - p) * -40}px)`, width: 1200}}>
              <div style={{fontFamily: condensed, fontSize: 36, color: C.red, width: 60}}>{String(i + 1).padStart(2, '0')}</div>
              <div style={{fontFamily: sans, fontWeight: 600, fontSize: 40, color: C.ink}}>{l}</div>
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
