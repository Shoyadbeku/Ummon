import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ANTON, C, MONT, accent} from '../theme';
import {Shot, ShotProps} from './Shot';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return {f, fps, sec: (s: number) => Math.round(s * fps)};
};

// =====================================================================
// PixelCity — generic top-down retro city illustration (original art)
// modes: top | chase | tilt (2D→3D) | sim (3D with live system labels)
// =====================================================================
const RX = [0, 1, 2, 3].map((j) => 90 + j * 300 + 35); // vertical road centers
const RY = [0, 1, 2, 3, 4, 5].map((i) => 160 + i * 360 + 35); // horizontal road centers

const loopPos = (d: number) => {
  // rectangular loop on roads: (RX1,RY1)->(RX2,RY1)->(RX2,RY3)->(RX1,RY3)
  const x1 = RX[1], x2 = RX[2], y1 = RY[1], y2 = RY[3];
  const w = x2 - x1, h = y2 - y1, P = 2 * (w + h);
  let p = ((d % P) + P) % P;
  if (p < w) return {x: x1 + p, y: y1, a: 0};
  p -= w;
  if (p < h) return {x: x2, y: y1 + p, a: 90};
  p -= h;
  if (p < w) return {x: x2 - p, y: y2, a: 180};
  p -= w;
  return {x: x1, y: y2 - p, a: 270};
};

const Car: React.FC<{x: number; y: number; a: number; color: string; police?: boolean; f: number; s?: number}> = ({x, y, a, color, police, f, s = 1}) => (
  <g transform={`translate(${x},${y}) rotate(${a}) scale(${s})`}>
    <rect x={-26} y={-14} width={52} height={28} rx={6} fill={color} stroke="#000" strokeWidth={3} />
    <rect x={2} y={-10} width={14} height={20} rx={3} fill="rgba(0,0,0,.45)" />
    {police && (
      <>
        <rect x={-8} y={-12} width={8} height={11} fill={f % 8 < 4 ? '#ff2b4a' : '#2b6bff'} />
        <rect x={-8} y={1} width={8} height={11} fill={f % 8 < 4 ? '#2b6bff' : '#ff2b4a'} />
        <circle r={60} fill={f % 8 < 4 ? 'rgba(255,43,74,.18)' : 'rgba(43,107,255,.18)'} />
      </>
    )}
  </g>
);

export const PixelCity: React.FC<{mode?: 'top' | 'chase' | 'tilt' | 'sim'; labels?: {text: string; at: number; x: number; y: number}[]; rainAt?: number}> = ({mode = 'top', labels = [], rainAt}) => {
  const {f, fps} = useT();
  const tiltP = mode === 'tilt' ? interpolate(f, [fps * 1.5, fps * 4], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)}) : mode === 'sim' ? 1 : 0;
  const speed = mode === 'chase' ? 9 : 6;
  const player = loopPos(f * speed);
  const cops = mode === 'chase' ? [70, 140, 210] : mode === 'top' ? [160] : [120, 220];
  const buildings: {x: number; y: number; w: number; h: number; c: string; z: number}[] = [];
  for (let j = 0; j < 4; j++)
    for (let i = 0; i < 6; i++) {
      const bx = 90 + j * 300 + 70, by = 160 + i * 360 + 70;
      const cw = 230, ch = 290;
      for (let k = 0; k < 4; k++) {
        const r = random(`b${i}${j}${k}`);
        const w = 70 + r * 40, h = 80 + random(`h${i}${j}${k}`) * 50;
        const x = bx + (k % 2) * (cw / 2) + 8, y = by + Math.floor(k / 2) * (ch / 2) + 8;
        const pal = ['#3a3f52', '#4b3a52', '#2f4a4a', '#55473a', '#3a4a5e', '#5e3a3a'];
        buildings.push({x, y, w: Math.min(w, cw / 2 - 16), h: Math.min(h, ch / 2 - 16), c: pal[Math.floor(r * pal.length)], z: 20 + random(`z${i}${j}${k}`) * 90});
      }
    }
  const traffic = RY.flatMap((y, i) => [0, 1, 2].map((k) => {
    const dir = i % 2 ? 1 : -1;
    const x = ((random(`t${i}${k}`) * 1300 + f * (3 + k) * dir) % 1300 + 1300) % 1300 - 110;
    return {x, y: y + (dir > 0 ? 14 : -14), a: dir > 0 ? 0 : 180, c: ['#e8e8e8', '#3fa7ff', '#ff8a00', '#9bff6b'][(i + k) % 4]};
  }));
  const peds = Array.from({length: 26}, (_, i) => {
    const vy = RY[i % 6] + (i % 2 ? 42 : -42);
    const x = ((random(`p${i}`) * 1100 + f * (i % 2 ? 1.2 : -1.2)) % 1100 + 1100) % 1100;
    return {x, y: vy};
  });
  const zoom = mode === 'chase' ? interpolate(f, [0, 200], [1.25, 1.4]) : interpolate(f, [0, 300], [1.1, 1.22]);
  const cam = mode === 'top' || mode === 'chase' ? {x: 540 - player.x, y: 900 - player.y} : {x: 0, y: 0};
  const camX = interpolate(tiltP, [0, 1], [cam.x * 0.6, 0]);
  const camY = interpolate(tiltP, [0, 1], [cam.y * 0.6, -120]);
  return (
    <AbsoluteFill style={{background: '#14161c', overflow: 'hidden', perspective: 1300}}>
      <AbsoluteFill style={{transform: `translateY(${tiltP * 160}px) rotateX(${tiltP * 52}deg) scale(${zoom + tiltP * 0.25}) translate(${camX}px, ${camY}px)`, transformOrigin: '50% 60%'}}>
        <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{imageRendering: 'pixelated'}}>
          <rect width={1080} height={1920} fill="#1d2a1f" />
          {RX.map((x, i) => <rect key={`v${i}`} x={x - 35} y={0} width={70} height={1920} fill="#2b2d33" />)}
          {RY.map((y, i) => <rect key={`h${i}`} x={0} y={y - 35} width={1080} height={70} fill="#2b2d33" />)}
          {RX.map((x, i) => <line key={`vl${i}`} x1={x} y1={0} x2={x} y2={1920} stroke="#d9c25a" strokeWidth={3} strokeDasharray="22 18" opacity={0.6} />)}
          {RY.map((y, i) => <line key={`hl${i}`} x1={0} y1={y} x2={1080} y2={y} stroke="#d9c25a" strokeWidth={3} strokeDasharray="22 18" opacity={0.6} />)}
          {peds.map((p, i) => <rect key={`p${i}`} x={p.x} y={p.y} width={8} height={8} fill={['#ffd166', '#ef476f', '#06d6a0', '#fff'][i % 4]} />)}
          {buildings.map((b, i) => {
            const k = tiltP * b.z;
            return (
              <g key={i}>
                {k > 1 && <rect x={b.x} y={b.y - k} width={b.w} height={b.h + k} fill="#000" opacity={0.55} />}
                {k > 1 && <rect x={b.x} y={b.y + b.h - k} width={b.w} height={k} fill={b.c} style={{filter: 'brightness(.6)'}} />}
                <rect x={b.x} y={b.y - k} width={b.w} height={b.h} fill={b.c} stroke="#0b0b10" strokeWidth={3} />
                <rect x={b.x + 8} y={b.y - k + 8} width={b.w - 16} height={6} fill="rgba(255,255,255,.12)" />
                {tiltP > 0.5 && f % 40 < 30 && <rect x={b.x + 12} y={b.y - k + 20} width={10} height={10} fill="#ffe08a" opacity={0.7} />}
              </g>
            );
          })}
          {traffic.map((t, i) => <Car key={`t${i}`} x={t.x} y={t.y} a={t.a} color={t.c} f={f} s={0.85} />)}
          {cops.map((g, i) => {
            const p = loopPos(f * speed - g);
            return <Car key={`c${i}`} x={p.x} y={p.y} a={p.a} color="#f4f4f4" police f={f + i * 3} />;
          })}
          <Car x={player.x} y={player.y} a={player.a} color={C.yellow} f={f} s={1.1} />
          <circle cx={player.x} cy={player.y} r={46 + Math.sin(f / 5) * 6} fill="none" stroke={C.yellow} strokeWidth={4} opacity={0.6} />
        </svg>
      </AbsoluteFill>
      {rainAt !== undefined && f > rainAt * fps && (
        <AbsoluteFill style={{opacity: interpolate(f, [rainAt * fps, rainAt * fps + 15], [0, 0.6], clamp)}}>
          <svg width={1080} height={1920}>
            {Array.from({length: 120}, (_, i) => {
              const x = random(`r${i}`) * 1200 - 60;
              const y = ((random(`ry${i}`) * 1920 + f * 48) % 2000) - 80;
              return <line key={i} x1={x} y1={y} x2={x - 10} y2={y + 46} stroke="rgba(180,210,255,.7)" strokeWidth={2.5} />;
            })}
          </svg>
        </AbsoluteFill>
      )}
      {labels.map((l, i) => {
        const s = spring({frame: f - l.at * fps, fps, config: {damping: 12, stiffness: 200}});
        if (f < l.at * fps) return null;
        return (
          <div key={i} style={{position: 'absolute', left: l.x, top: l.y, transform: `scale(${s})`, transformOrigin: 'left center'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div style={{width: 22, height: 22, borderRadius: 11, background: C.yellow, boxShadow: `0 0 20px ${C.yellow}`}} />
              <div style={{background: '#000d', border: `3px solid ${C.yellow}`, padding: '8px 18px', borderRadius: 10, fontFamily: MONT, fontWeight: 900, fontSize: 40, color: '#fff', textTransform: 'uppercase'}}>{l.text}</div>
            </div>
          </div>
        );
      })}
      <AbsoluteFill style={{background: 'repeating-linear-gradient(0deg, rgba(0,0,0,.18) 0 2px, transparent 2px 4px)', mixBlendMode: 'multiply'}} />
    </AbsoluteFill>
  );
};

// =====================================================================
// LogoCard — logo reveal with glow + light sweep
// =====================================================================
export const LogoCard: React.FC<{src: string; sub?: string; color?: string; width?: number; bg?: ShotProps & {dur?: number}; dur: number}> = ({src, sub, color, width = 760, bg, dur}) => {
  const {f, fps} = useT();
  const ac = accent(color);
  const s = spring({frame: f, fps, config: {damping: 15, stiffness: 110}});
  const sweep = interpolate(f, [8, 38], [-60, 160], clamp);
  return (
    <AbsoluteFill style={{background: `radial-gradient(circle at 50% 38%, ${ac}33 0%, #07070c 62%)`}}>
      {bg && <AbsoluteFill style={{opacity: 0.35}}><Shot {...bg} dur={dur} /></AbsoluteFill>}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'flex-start', paddingTop: 300}}>
        <div style={{position: 'relative', width, transform: `scale(${interpolate(s, [0, 1], [1.35, 1]) + f * 0.0008})`, filter: `blur(${interpolate(s, [0, 0.8], [18, 0], clamp)}px) drop-shadow(0 0 50px ${ac}88)`, opacity: interpolate(s, [0, 0.3], [0, 1], clamp)}}>
          <Img src={staticFile(src)} style={{width: '100%'}} />
          <div style={{position: 'absolute', inset: 0, background: `linear-gradient(105deg, transparent ${sweep - 15}%, rgba(255,255,255,.55) ${sweep}%, transparent ${sweep + 15}%)`, mixBlendMode: 'overlay', WebkitMaskImage: `url(${staticFile(src)})`, WebkitMaskSize: '100% 100%'}} />
        </div>
        {sub && (
          <div style={{marginTop: 36, fontFamily: MONT, fontWeight: 900, fontSize: 48, letterSpacing: 8, color: ac, textTransform: 'uppercase', opacity: interpolate(f, [14, 26], [0, 1], clamp), textShadow: '0 4px 20px #000'}}>{sub}</div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// =====================================================================
// SplitScreen — top vs bottom comparison
// =====================================================================
export const Split: React.FC<{a: ShotProps & {label: string}; b: ShotProps & {label: string}; bAt?: number; dur: number; color?: string}> = ({a, b, bAt = 0, dur, color}) => {
  const {f, fps} = useT();
  const ac = accent(color);
  const sA = spring({frame: f, fps, config: {damping: 16, stiffness: 120}});
  const sB = spring({frame: f - bAt * fps, fps, config: {damping: 16, stiffness: 120}});
  const half = (p: ShotProps & {label: string}, top: boolean, s: number, col: string) => (
    <div style={{position: 'absolute', left: 0, right: 0, top: top ? 0 : 1000, height: 920, overflow: 'hidden', clipPath: `inset(0 ${top ? (1 - s) * 100 : 0}% 0 ${top ? 0 : (1 - s) * 100}%)`}}>
      <div style={{position: 'absolute', inset: 0}}><Shot {...p} dur={dur} /></div>
      <div style={{position: 'absolute', left: 60, [top ? 'top' : 'bottom']: top ? 200 : 380, background: col, padding: '10px 24px', borderRadius: 8, fontFamily: MONT, fontWeight: 900, fontSize: 50, color: '#000', textTransform: 'uppercase'}}>{p.label}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {half(a, true, sA, '#fff')}
      {f >= bAt * fps && half(b, false, sB, ac)}
      <div style={{position: 'absolute', left: 0, right: 0, top: 920, height: 80, background: '#000'}} />
      <div style={{position: 'absolute', left: 540 - 70, top: 890, width: 140, height: 140, borderRadius: 70, background: ac, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 64, color: '#000', transform: `scale(${sB})`, boxShadow: `0 0 50px ${ac}`}}>VS</div>
    </AbsoluteFill>
  );
};

// =====================================================================
// Icon set (simple strokes) + IconGrid
// =====================================================================
const ICONS: Record<string, React.ReactNode> = {
  gym: <path d="M3 9v6M6 7v10M18 7v10M21 9v6M6 12h12" />,
  food: <path d="M7 3v8a2 2 0 002 2v8M7 3v5M11 3v5M17 3c-2 2-2 6 0 8v10" />,
  shirt: <path d="M8 3l-5 3 2 4 3-1v12h8V9l3 1 2-4-5-3a4 4 0 01-8 0z" />,
  hair: <path d="M6 6a3 3 0 110 0M6 18a3 3 0 110 0M8.5 7.5L20 18M8.5 16.5L20 6" />,
  car: <path d="M3 13l2-6h14l2 6v5H3zM3 13h18M7 18v2M17 18v2M7 15.5h.01M17 15.5h.01" />,
  city: <path d="M3 21V9l6-3v15M9 21V3h8v18M17 21V11h4v10M12 7h2M12 11h2M12 15h2" />,
  cube: <path d="M12 2l9 5v10l-9 5-9-5V7zM12 12l9-5M12 12v10M12 12L3 7" />,
  brain: <path d="M9 3a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 006 2V3zM15 3a3 3 0 013 3 3 3 0 012 5 3 3 0 01-2 5 3 3 0 01-6 2" />,
  light: <path d="M9 18h6M10 21h4M12 3a6 6 0 00-4 10c1 1 1 2 1 3h6c0-1 0-2 1-3a6 6 0 00-4-10z" />,
  mic: <path d="M12 3a3 3 0 013 3v6a3 3 0 01-6 0V6a3 3 0 013-3zM5 11a7 7 0 0014 0M12 18v3" />,
  film: <path d="M3 4h18v16H3zM7 4v16M17 4v16M3 8h4M3 12h4M3 16h4M17 8h4M17 12h4M17 16h4" />,
  book: <path d="M4 4h7a3 3 0 013 3v14a2 2 0 00-2-2H4zM20 4h-6M20 4v15h-6" />,
  users: <path d="M9 11a4 4 0 100-8 4 4 0 000 8zM2 21a7 7 0 0114 0M17 11a3 3 0 100-6M22 21a6 6 0 00-5-6" />,
  cart: <path d="M3 3h3l3 12h10l2-8H7M10 20h.01M18 20h.01" />,
  briefcase: <path d="M3 7h18v13H3zM8 7V4h8v3M3 12h18" />,
  trophy: <path d="M8 4h8v6a4 4 0 01-8 0zM8 6H4a4 4 0 004 4M16 6h4a4 4 0 01-4 4M12 14v4M8 21h8" />,
  mount: <path d="M2 20l7-12 4 6 3-4 6 10z" />,
  wave: <path d="M2 12c3-3 5 3 8 0s5 3 8 0 4 0 4 0M2 17c3-3 5 3 8 0s5 3 8 0" />,
  plane: <path d="M2 14l20-8-6 15-3-6-6-1zM13 15l9-9" />,
  sun: <path d="M12 7a5 5 0 110 10 5 5 0 010-10zM12 1v3M12 20v3M1 12h3M20 12h3M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2" />,
  target: <path d="M12 3a9 9 0 110 18 9 9 0 010-18zM12 8a4 4 0 110 8 4 4 0 010-8z" />,
  eye: <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 9a3 3 0 110 6 3 3 0 010-6z" />,
  play: <path d="M6 4l14 8-14 8z" />,
  chat: <path d="M4 4h16v12H8l-4 4z" />,
};
export const Icon: React.FC<{name: string; size?: number; color?: string}> = ({name, size = 56, color = '#000'}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">{ICONS[name]}</svg>
);

export const IconGrid: React.FC<{title?: string; items: {label: string; icon: string; at: number}[]; color?: string; linkAt?: number; top?: number}> = ({title, items, color, linkAt, top = 250}) => {
  const {f, fps} = useT();
  const ac = accent(color);
  const cols = 2;
  const tileW = 440, tileH = items.length > 6 ? 170 : 200, gap = 26;
  const pos = (i: number) => ({x: 70 + (i % cols) * (tileW + gap), y: top + (title ? 110 : 0) + Math.floor(i / cols) * (tileH + gap)});
  const linkP = linkAt !== undefined ? interpolate(f, [linkAt * fps, linkAt * fps + 30], [0, 1], clamp) : 0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {title && <div style={{position: 'absolute', top, left: 70, right: 70, fontFamily: ANTON, fontSize: 84, color: '#fff', textTransform: 'uppercase', textShadow: '0 8px 30px #000'}}>{title}</div>}
      {linkP > 0 && (
        <svg width={1080} height={1920} style={{position: 'absolute'}}>
          {items.map((_, i) => items.map((__, j) => {
            if (j <= i) return null;
            const a = pos(i), b = pos(j);
            return <line key={`${i}-${j}`} x1={a.x + tileW / 2} y1={a.y + tileH / 2} x2={a.x + tileW / 2 + (b.x - a.x) * linkP} y2={a.y + tileH / 2 + (b.y - a.y) * linkP} stroke={ac} strokeWidth={2} opacity={0.5} />;
          }))}
        </svg>
      )}
      {items.map((it, i) => {
        const s = spring({frame: f - it.at * fps, fps, config: {damping: 13, stiffness: 190}});
        if (f < it.at * fps) return null;
        const {x, y} = pos(i);
        const glow = linkP > 0 ? 0.5 + 0.5 * Math.sin(f / 4 + i) : 0;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, width: tileW, height: tileH, borderRadius: 24, background: 'rgba(10,10,18,.86)', border: `3px solid ${ac}`, boxShadow: `0 0 ${20 + glow * 30}px ${ac}66`, display: 'flex', alignItems: 'center', gap: 22, padding: '0 26px', transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`, opacity: s}}>
            <div style={{width: 92, height: 92, borderRadius: 20, background: ac, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}><Icon name={it.icon} /></div>
            <div style={{fontFamily: MONT, fontWeight: 900, fontSize: it.label.length > 12 ? 34 : 40, color: '#fff', textTransform: 'uppercase', lineHeight: 1.05}}>{it.label}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// TimedList — list items appear at given seconds
// =====================================================================
export const TimedList: React.FC<{title?: string; items: {text: string; at: number}[]; color?: string; top?: number; size?: number}> = ({title, items, color, top = 300, size = 60}) => {
  const {f, fps} = useT();
  const ac = accent(color);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 80, right: 80}}>
        {title && <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 44, color: ac, letterSpacing: 6, textTransform: 'uppercase', marginBottom: 24, textShadow: '0 4px 20px #000'}}>{title}</div>}
        {items.map((it, i) => {
          if (f < it.at * fps) return null;
          const s = spring({frame: f - it.at * fps, fps, config: {damping: 14, stiffness: 180}});
          const latest = items.filter((x) => f >= x.at * fps).length - 1 === i;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 24, marginBottom: 22, opacity: s, transform: `translateX(${interpolate(s, [0, 1], [-140, 0])}px)`}}>
              <div style={{fontFamily: ANTON, fontSize: size * 0.9, color: latest ? '#000' : ac, background: latest ? ac : 'transparent', border: `4px solid ${ac}`, width: size * 1.3, height: size * 1.3, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: size, color: '#fff', textTransform: 'uppercase', textShadow: '0 6px 24px #000', lineHeight: 1.02}}>{it.text}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// Panels — N vertical panels revealed at times
// =====================================================================
export const Panels: React.FC<{panels: (ShotProps & {name: string; at: number; color?: string})[]; dur: number}> = ({panels, dur}) => {
  const {f, fps} = useT();
  const w = 1080 / panels.length;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {panels.map((p, i) => {
        const s = spring({frame: f - p.at * fps, fps, config: {damping: 18, stiffness: 120}});
        if (f < p.at * fps) return null;
        const ac = accent(p.color);
        return (
          <div key={i} style={{position: 'absolute', left: i * w, top: 0, width: w - 6, height: 1920, overflow: 'hidden', clipPath: `inset(${(1 - s) * 100}% 0 0 0)`}}>
            <div style={{position: 'absolute', left: -(1080 - w) / 2, width: 1080, height: 1920}}><Shot {...p} dur={dur} /></div>
            <div style={{position: 'absolute', inset: 0, background: `linear-gradient(180deg, ${ac}55, transparent 40%)`}} />
            <div style={{position: 'absolute', top: 260, left: 0, right: 0, textAlign: 'center', fontFamily: ANTON, fontSize: 70, color: '#fff', textTransform: 'uppercase', textShadow: '0 6px 24px #000', transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`}}>{p.name}</div>
            <div style={{position: 'absolute', top: 350, left: w / 2 - 50, width: 100, height: 8, background: ac, borderRadius: 4}} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// HackUI — cyber attack / leak terminal
// =====================================================================
export const HackUI: React.FC<{lines: string[]; title: string}> = ({lines, title}) => {
  const {f} = useT();
  const flick = f % 14 < 9;
  const chars = Math.floor(f * 2.2);
  let used = 0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 260, left: 60, right: 60, background: 'rgba(5,10,8,.9)', border: '2px solid #2bff88', borderRadius: 18, boxShadow: '0 0 60px rgba(43,255,136,.25)', overflow: 'hidden', transform: `translateX(${f < 10 ? (random(f) - 0.5) * 30 : 0}px)`}}>
        <div style={{display: 'flex', gap: 10, padding: '14px 18px', background: '#0f1a14', borderBottom: '2px solid #2bff8855'}}>
          {['#ff5f56', '#ffbd2e', '#27c93f'].map((c) => <div key={c} style={{width: 18, height: 18, borderRadius: 9, background: c}} />)}
          <div style={{marginLeft: 16, fontFamily: 'monospace', fontSize: 26, color: '#2bff88'}}>terminal — secure_server</div>
        </div>
        <div style={{padding: '22px 28px', fontFamily: 'monospace', fontSize: 36, lineHeight: 1.45, color: '#2bff88', minHeight: 420}}>
          {lines.map((l, i) => {
            const show = Math.max(0, Math.min(l.length, chars - used));
            used += l.length;
            if (show <= 0) return null;
            return <div key={i} style={{color: l.startsWith('!') ? '#ff3b5c' : '#2bff88'}}>{l.slice(0, show)}{show < l.length && <span>█</span>}</div>;
          })}
        </div>
      </div>
      <div style={{position: 'absolute', top: 820, left: 60, right: 60, textAlign: 'center', opacity: f > 30 ? (flick ? 1 : 0.35) : 0}}>
        <div style={{display: 'inline-block', background: '#ff1f45', padding: '14px 34px', borderRadius: 10, fontFamily: ANTON, fontSize: 86, color: '#fff', letterSpacing: 4, boxShadow: '0 0 60px #ff1f45'}}>⚠ {title}</div>
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// TrailerUI — video player card with logo and play animation
// =====================================================================
export const TrailerUI: React.FC<{logo: string; label: string}> = ({logo, label}) => {
  const {f, fps} = useT();
  const s = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
  const pressed = f > 22;
  const prog = interpolate(f, [24, 110], [0, 0.85], clamp);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 35%, #3a1450 0%, #08060c 70%)'}}>
      <div style={{position: 'absolute', top: 300, left: 50, right: 50, height: 560, borderRadius: 28, overflow: 'hidden', background: 'linear-gradient(135deg,#ff6a3d,#c2247c 45%,#3b1d8f)', boxShadow: '0 40px 120px rgba(0,0,0,.8)', transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})`, opacity: s}}>
        <Img src={staticFile(logo)} style={{position: 'absolute', left: '50%', top: '50%', width: 520, transform: `translate(-50%,-55%) scale(${1 + f * 0.0015})`, filter: 'drop-shadow(0 10px 30px rgba(0,0,0,.5))', opacity: pressed ? 1 : 0.5}} />
        {!pressed && (
          <div style={{position: 'absolute', left: '50%', top: '50%', width: 170, height: 170, borderRadius: 85, background: 'rgba(0,0,0,.6)', transform: `translate(-50%,-50%) scale(${f > 16 ? 0.85 : 1})`, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '4px solid #fff'}}>
            <Icon name="play" size={80} color="#fff" />
          </div>
        )}
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 14, background: 'rgba(255,255,255,.25)'}}>
          <div style={{width: `${prog * 100}%`, height: '100%', background: '#ff2040'}} />
        </div>
      </div>
      <div style={{position: 'absolute', top: 900, left: 0, right: 0, textAlign: 'center', fontFamily: MONT, fontWeight: 900, fontSize: 46, color: C.yellow, letterSpacing: 6, textTransform: 'uppercase', opacity: interpolate(f, [10, 20], [0, 1], clamp)}}>{label}</div>
    </AbsoluteFill>
  );
};

// =====================================================================
// DateShift — release dates moved, crossed out, final date confirmed
// =====================================================================
export const DateShift: React.FC<{items: {text: string; at: number; crossAt?: number}[]; final: {text: string; at: number; sub: string}}> = ({items, final}) => {
  const {f, fps} = useT();
  const finalOn = f >= final.at * fps;
  const fs = spring({frame: f - final.at * fps, fps, config: {damping: 10, stiffness: 160}});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 35%, #1b2236 0%, #06070c 70%)'}}>
      <div style={{position: 'absolute', top: 210, left: 0, right: 0, textAlign: 'center', fontFamily: MONT, fontWeight: 900, fontSize: 46, letterSpacing: 8, color: C.muted, textTransform: 'uppercase'}}>Chiqish sanasi</div>
      <div style={{position: 'absolute', top: 300, left: 110, right: 110, opacity: finalOn ? interpolate(f, [final.at * fps, final.at * fps + 10], [1, 0.15], clamp) : 1}}>
        {items.map((it, i) => {
          if (f < it.at * fps) return null;
          const s = spring({frame: f - it.at * fps, fps, config: {damping: 14, stiffness: 170}});
          const cp = it.crossAt !== undefined ? interpolate(f, [it.crossAt * fps, it.crossAt * fps + 8], [0, 1], clamp) : 0;
          const ok = it.crossAt === undefined;
          return (
            <div key={i} style={{position: 'relative', marginBottom: 34, padding: '26px 36px', borderRadius: 22, background: ok ? 'rgba(61,255,138,.12)' : 'rgba(255,255,255,.06)', border: `4px solid ${ok ? C.green : cp > 0 ? C.pink : 'rgba(255,255,255,.3)'}`, transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`, opacity: s, display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
              <div style={{fontFamily: ANTON, fontSize: 96, color: ok ? C.green : '#fff', opacity: cp > 0 ? 0.5 : 1}}>{it.text}</div>
              <div style={{fontFamily: ANTON, fontSize: 90, color: ok ? C.green : C.pink, transform: `scale(${ok ? s : cp})`}}>{ok ? '✓' : '✕'}</div>
              {cp > 0 && <div style={{position: 'absolute', left: 30, top: '50%', height: 10, width: `${cp * 70}%`, background: C.pink, borderRadius: 5, transform: 'rotate(-4deg)'}} />}
            </div>
          );
        })}
      </div>
      {finalOn && (
        <div style={{position: 'absolute', top: 430, left: 0, right: 0, textAlign: 'center', transform: `scale(${interpolate(fs, [0, 1], [1.8, 1])})`, opacity: Math.min(1, fs * 2)}}>
          <div style={{display: 'inline-block', padding: '30px 50px', borderRadius: 30, border: `8px solid ${C.green}`, background: '#03140acc', boxShadow: `0 0 80px ${C.green}88`}}>
            <div style={{fontFamily: ANTON, fontSize: 170, color: C.green, lineHeight: 1}}>{final.text}</div>
            <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 50, color: '#fff', textTransform: 'uppercase', marginTop: 10}}>{final.sub}</div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// =====================================================================
// Platforms — GTA VI with console images and feature chips
// =====================================================================
export const Platforms: React.FC<{chips: {text: string; at: number}[]; imgsAt: number}> = ({chips, imgsAt}) => {
  const {f, fps} = useT();
  const s = spring({frame: f, fps, config: {damping: 15}});
  const si = spring({frame: f - imgsAt * fps, fps, config: {damping: 14}});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 30%, #2a1840 0%, #07060b 70%)'}}>
      <Img src={staticFile('img/logo_gta6.png')} style={{position: 'absolute', top: 190, left: 300, width: 480, opacity: s, transform: `scale(${interpolate(s, [0, 1], [1.2, 1])})`}} />
      <div style={{position: 'absolute', top: 600, left: 40, right: 40, display: 'flex', gap: 30, justifyContent: 'center', opacity: si, transform: `translateY(${interpolate(si, [0, 1], [80, 0])}px)`}}>
        <div style={{width: 470, height: 360, borderRadius: 24, background: '#fff', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Img src={staticFile('img/ps5.png')} style={{height: 340}} />
        </div>
        <div style={{width: 470, height: 360, borderRadius: 24, overflow: 'hidden'}}>
          <Img src={staticFile('img/xbox_series.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '70% 50%'}} />
        </div>
      </div>
      <div style={{position: 'absolute', top: 990, left: 40, right: 40, display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center'}}>
        {chips.map((c, i) => {
          if (f < c.at * fps) return null;
          const cs = spring({frame: f - c.at * fps, fps, config: {damping: 12, stiffness: 220}});
          return <div key={i} style={{transform: `scale(${cs})`, background: i % 2 ? C.pink : C.yellow, color: '#000', borderRadius: 40, padding: '10px 26px', fontFamily: MONT, fontWeight: 900, fontSize: 36, textTransform: 'uppercase'}}>{c.text}</div>;
        })}
      </div>
    </AbsoluteFill>
  );
};

// =====================================================================
// TimelineRecap — vertical history timeline
// =====================================================================
export const TimelineRecap: React.FC<{items: {year: string; title: string; at: number; color?: string}[]}> = ({items}) => {
  const {f, fps} = useT();
  const shown = items.filter((i) => f >= i.at * fps);
  const lineH = interpolate(f, [0, items[items.length - 1].at * fps + 20], [0, 1], clamp);
  const top = 200, step = 128;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 30% 30%, #18202e 0%, #06070b 75%)'}}>
      <div style={{position: 'absolute', left: 300, top: top + 20, width: 6, height: (items.length - 1) * step * lineH, background: `linear-gradient(${C.yellow}, ${C.pink})`, borderRadius: 3}} />
      {items.map((it, i) => {
        if (f < it.at * fps) return null;
        const s = spring({frame: f - it.at * fps, fps, config: {damping: 13, stiffness: 180}});
        const active = shown.length - 1 === i;
        const ac = accent(it.color);
        return (
          <div key={i} style={{position: 'absolute', top: top + i * step, left: 0, right: 0, height: step, opacity: active ? s : 0.55}}>
            <div style={{position: 'absolute', right: 1080 - 260, top: 0, fontFamily: ANTON, fontSize: active ? 80 : 64, color: active ? ac : '#fff', textAlign: 'right', transform: `translateX(${interpolate(s, [0, 1], [-60, 0])}px)`}}>{it.year}</div>
            <div style={{position: 'absolute', left: 290, top: 18, width: 26, height: 26, borderRadius: 13, background: active ? ac : '#fff', boxShadow: active ? `0 0 30px ${ac}` : 'none', transform: `scale(${active ? 1.3 : 1})`}} />
            <div style={{position: 'absolute', left: 350, top: 4, fontFamily: MONT, fontWeight: 900, fontSize: active ? 60 : 48, color: '#fff', textTransform: 'uppercase', transform: `translateX(${interpolate(s, [0, 1], [60, 0])}px)`, textShadow: '0 4px 18px #000'}}>{it.title}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// =====================================================================
// Poll — viewer question card
// =====================================================================
export const Poll: React.FC<{q: string; options: {text: string; at: number}[]; ctaAt: number}> = ({q, options, ctaAt}) => {
  const {f, fps} = useT();
  const s = spring({frame: f, fps, config: {damping: 15}});
  const cta = spring({frame: f - ctaAt * fps, fps, config: {damping: 9, stiffness: 200}});
  const latest = options.filter((o) => f >= o.at * fps).length - 1;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 30%, #2d1a3f 0%, #07060b 70%)'}}>
      <div style={{position: 'absolute', top: 200, left: 60, right: 60, padding: 40, borderRadius: 32, background: 'rgba(255,255,255,.06)', border: '2px solid rgba(255,255,255,.15)', transform: `scale(${interpolate(s, [0, 1], [0.9, 1])})`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 76, color: '#fff', textTransform: 'uppercase', lineHeight: 1.05, marginBottom: 30}}>{q}</div>
        {options.map((o, i) => {
          if (f < o.at * fps) return null;
          const os = spring({frame: f - o.at * fps, fps, config: {damping: 14, stiffness: 200}});
          const on = i === latest;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, padding: '20px 26px', marginBottom: 16, borderRadius: 18, background: on ? C.yellow : 'rgba(255,255,255,.08)', transform: `translateX(${interpolate(os, [0, 1], [100, 0])}px)`, opacity: os}}>
              <div style={{width: 40, height: 40, borderRadius: 20, border: `5px solid ${on ? '#000' : '#fff'}`, background: on ? '#000' : 'transparent'}} />
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 50, color: on ? '#000' : '#fff', textTransform: 'uppercase'}}>{o.text}</div>
            </div>
          );
        })}
      </div>
      {f >= ctaAt * fps && (
        <div style={{position: 'absolute', top: 960, left: 0, right: 0, display: 'flex', justifyContent: 'center', transform: `scale(${cta * (1 + 0.04 * Math.sin(f / 4))})`}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18, background: C.pink, padding: '16px 36px', borderRadius: 60, boxShadow: `0 0 50px ${C.pink}`}}>
            <Icon name="chat" size={54} color="#fff" />
            <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 46, color: '#fff', textTransform: 'uppercase'}}>Izohlarda yozing</div>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// Big full-screen word on solid background (pattern interrupt)
export const BigWord: React.FC<{text: string; color?: string; bg?: string; size?: number}> = ({text, color, bg = '#000', size = 260}) => {
  const {f, fps} = useT();
  const s = spring({frame: f, fps, config: {damping: 9, stiffness: 260}});
  return (
    <AbsoluteFill style={{background: bg, alignItems: 'center', justifyContent: 'center'}}>
      <div style={{marginTop: -300, fontFamily: ANTON, fontSize: size, color: accent(color), textTransform: 'uppercase', transform: `scale(${interpolate(s, [0, 1], [2.2, 1])})`, textShadow: `0 0 80px ${accent(color)}88`, textAlign: 'center', lineHeight: 0.95, padding: '0 40px'}}>{text}</div>
    </AbsoluteFill>
  );
};
