import React from 'react';
import {
  AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, random, Sequence, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

// Fonts are bundled locally (public/fonts, from Google Fonts, SIL OFL) so rendering works offline.
export const ANTON = 'Anton';
export const MONT = 'Montserrat';
if (typeof document !== 'undefined' && !document.getElementById('local-fonts')) {
  const st = document.createElement('style');
  st.id = 'local-fonts';
  st.innerHTML = `@font-face{font-family:'Anton';font-weight:400;src:url(${staticFile('fonts/Anton-400-latin.woff2')}) format('woff2');}
@font-face{font-family:'Montserrat';font-weight:700 900;src:url(${staticFile('fonts/Montserrat-900-latin.woff2')}) format('woff2');}`;
  document.head.appendChild(st);
  (document as any).fonts.load("400 40px 'Anton'"); (document as any).fonts.load("900 40px 'Montserrat'");
}

export const FPS = 30;
export const f = (sec: number) => Math.round(sec * FPS);
export const OVER = 8; // frames each shot lingers under the next one (no black gaps)

export const GOLD = '#FFD23F';
export const YELLOW = '#FFE81A';
export const GREEN = '#3DFF8A';
export const RED = '#FF3B3B';
export const CYAN = '#4FE3FF';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

type Enter = 'cut' | 'whip-up' | 'whip-down' | 'whip-left' | 'whip-right' | 'zoom' | 'fade' | 'flash' | 'mask';

const GRADES: Record<string, string> = {
  none: 'contrast(1.08) saturate(1.08)',
  cine: 'contrast(1.15) saturate(1.12) brightness(0.95)',
  night: 'contrast(1.2) saturate(0.85) brightness(0.8) hue-rotate(-8deg)',
  warm: 'contrast(1.12) saturate(1.25) sepia(0.12)',
  bw: 'grayscale(1) contrast(1.35) brightness(0.9)',
  money: 'contrast(1.2) saturate(1.3) brightness(0.85)',
  dark: 'contrast(1.15) brightness(0.55) saturate(0.9)',
  dark2: 'contrast(1.18) brightness(0.72) saturate(0.95)',
  cool: 'contrast(1.12) saturate(1.05) hue-rotate(-8deg) brightness(0.95)',
  retro: 'sepia(0.45) contrast(1.15) saturate(0.85) brightness(0.92)',
};

/** One shot: video or photo, cropped to 9:16, with Ken Burns, grade and an entrance transition. */
export const Shot: React.FC<{
  src: string; img?: boolean; from: number; to: number; enter?: Enter;
  kb?: [number, number]; drift?: [number, number]; pos?: string; grade?: string;
  startFrom?: number; rate?: number; contain?: boolean; children?: React.ReactNode; tint?: string;
}> = ({src, img, from, to, enter = 'cut', kb = [1.08, 1.18], drift = [0, 0], pos = 'center', grade = 'cine', startFrom = 0, rate = 1, contain, children, tint}) => {
  const start = f(from);
  const dur = f(to) - start + OVER;
  return (
    <Sequence from={start} durationInFrames={dur} layout="none">
      <ShotInner {...{src, img, dur, enter, kb, drift, pos, grade, startFrom, rate, contain, tint}}>{children}</ShotInner>
    </Sequence>
  );
};

const ShotInner: React.FC<any> = ({src, img, dur, enter, kb, drift, pos, grade, startFrom, rate, contain, children, tint}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 9], [0, 1], {...clamp, easing: easeOut});
  const t = interpolate(frame, [0, dur], [0, 1], clamp);
  const scale = interpolate(t, [0, 1], kb);
  const dx = interpolate(t, [0, 1], [0, drift[0]]);
  const dy = interpolate(t, [0, 1], [0, drift[1]]);
  let tx = 0, ty = 0, sc = 1, blur = 0, op = 1, clip = 'none';
  if (enter === 'whip-up') { ty = (1 - p) * 1920; blur = (1 - p) * 40; }
  if (enter === 'whip-down') { ty = -(1 - p) * 1920; blur = (1 - p) * 40; }
  if (enter === 'whip-left') { tx = (1 - p) * 1080; blur = (1 - p) * 40; }
  if (enter === 'whip-right') { tx = -(1 - p) * 1080; blur = (1 - p) * 40; }
  if (enter === 'zoom') { sc = interpolate(p, [0, 1], [1.6, 1]); blur = (1 - p) * 30; op = p; }
  if (enter === 'fade') { op = p; }
  if (enter === 'mask') { clip = `circle(${p * 120}% at 50% 50%)`; }
  const media: React.CSSProperties = {width: '100%', height: '100%', objectFit: contain ? 'contain' : 'cover', objectPosition: pos};
  const el = img
    ? <Img src={staticFile(src)} style={media} />
    : <OffthreadVideo src={staticFile(src)} startFrom={Math.round(startFrom * FPS)} playbackRate={rate} muted style={media} />;
  return (
    <AbsoluteFill style={{transform: `translate(${tx}px, ${ty}px) scale(${sc})`, filter: blur ? `blur(${blur}px)` : undefined, opacity: op, clipPath: clip, overflow: 'hidden', backgroundColor: '#05060a'}}>
      {contain && (
        <AbsoluteFill style={{filter: 'blur(40px) brightness(0.45)', transform: 'scale(1.3)'}}>
          {img ? <Img src={staticFile(src)} style={{...media, objectFit: 'cover'}} /> : null}
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{transform: `scale(${scale}) translate(${dx}px, ${dy}px)`, filter: GRADES[grade] ?? grade}}>{el}</AbsoluteFill>
      {tint && <AbsoluteFill style={{background: tint, mixBlendMode: 'soft-light'}} />}
      {/* top/bottom gradient so text stays readable */}
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0) 28%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.65) 100%)'}} />
      {enter === 'flash' && <AbsoluteFill style={{backgroundColor: 'white', opacity: interpolate(frame, [0, 6], [1, 0], clamp)}} />}
      {children}
    </AbsoluteFill>
  );
};

/** Animated film grain (SVG turbulence with per-frame seed). */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.09}) => {
  const frame = useCurrentFrame();
  const seed = frame % 12;
  return (
    <AbsoluteFill style={{opacity, mixBlendMode: 'overlay', pointerEvents: 'none'}}>
      <svg width="1080" height="1920">
        <filter id={`g${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#g${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.6) 100%)', pointerEvents: 'none'}} />
);

/** Warm light leak sweeping across the frame (blend: screen). */
export const LightLeak: React.FC<{at: number; dur?: number; hue?: 'warm' | 'cool'}> = ({at, dur = 0.7, hue = 'warm'}) => (
  <Sequence from={f(at) - 4} durationInFrames={f(dur)} layout="none">
    <LeakInner dur={f(dur)} hue={hue} />
  </Sequence>
);
const LeakInner: React.FC<{dur: number; hue: string}> = ({dur, hue}) => {
  const frame = useCurrentFrame();
  const t = frame / dur;
  const op = interpolate(t, [0, 0.25, 0.6, 1], [0, 0.9, 0.6, 0]);
  const x = interpolate(t, [0, 1], [-30, 130]);
  const c1 = hue === 'warm' ? 'rgba(255,140,40,0.95)' : 'rgba(80,180,255,0.9)';
  const c2 = hue === 'warm' ? 'rgba(255,60,90,0.6)' : 'rgba(150,90,255,0.6)';
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: op, background: `radial-gradient(circle at ${x}% 40%, ${c1} 0%, ${c2} 25%, rgba(0,0,0,0) 55%)`}} />
  );
};

export const Flash: React.FC<{at: number; color?: string; len?: number}> = ({at, color = 'white', len = 7}) => (
  <Sequence from={f(at)} durationInFrames={len} layout="none">
    <FlashInner color={color} len={len} />
  </Sequence>
);
const FlashInner: React.FC<{color: string; len: number}> = ({color, len}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{backgroundColor: color, opacity: interpolate(frame, [0, len], [0.95, 0], clamp)}} />;
};

/** Camera shake wrapper active from `at` for `dur` seconds. */
export const Shake: React.FC<{at: number; dur?: number; amp?: number; children: React.ReactNode}> = ({at, dur = 0.4, amp = 18, children}) => {
  const frame = useCurrentFrame();
  const local = frame - f(at);
  const k = local >= 0 && local < f(dur) ? 1 - local / f(dur) : 0;
  const x = (random(`x${frame}`) - 0.5) * 2 * amp * k;
  const y = (random(`y${frame}`) - 0.5) * 2 * amp * k;
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px)`}}>{children}</AbsoluteFill>;
};

const txtShadow = '0 6px 0 rgba(0,0,0,0.55), 0 0 40px rgba(0,0,0,0.6)';

/** Kinetic headline: per-letter spring stagger, optional gradient fill. */
export const Headline: React.FC<{
  text: string; at: number; until: number; y: number; size?: number; color?: string;
  gradient?: string; font?: string; stagger?: number; tilt?: number; exit?: boolean; glow?: string; letterSpacing?: number;
}> = ({text, at, until, y, size = 150, color = 'white', gradient, font = ANTON, stagger = 1.2, tilt = 0, exit = true, glow, letterSpacing = 2}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <HeadlineInner {...{text, y, size, color, gradient, font, stagger, tilt, exit, glow, letterSpacing}} dur={f(until) - f(at)} />
  </Sequence>
);
const HeadlineInner: React.FC<any> = ({text, y, size, color, gradient, font, stagger, tilt, exit, glow, letterSpacing, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const out = exit ? interpolate(frame, [dur - 6, dur], [1, 0], clamp) : 1;
  const lines: string[] = text.split('\n');
  let idx = 0;
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', opacity: out, transform: `rotate(${tilt}deg)`}}>
      {lines.map((line, li) => (
        <div key={li} style={{display: 'flex', justifyContent: 'center', lineHeight: 1.0}}>
          {line.split('').map((ch, ci) => {
            const i = idx++;
            const s = spring({frame: frame - i * stagger, fps, config: {damping: 13, stiffness: 180, mass: 0.6}});
            return (
              <span key={ci} style={{
                display: 'inline-block', fontFamily: font, fontSize: size, color, letterSpacing,
                transform: `translateY(${(1 - s) * 80}px) scale(${0.4 + 0.6 * s})`, opacity: Math.min(1, s * 1.5),
                textShadow: gradient ? undefined : txtShadow, whiteSpace: 'pre',
                ...(gradient ? {backgroundImage: gradient, WebkitBackgroundClip: 'text', backgroundClip: 'text', WebkitTextFillColor: 'transparent', filter: `drop-shadow(0 6px 0 rgba(0,0,0,0.6)) ${glow ? `drop-shadow(0 0 30px ${glow})` : ''}`} : {}),
              }}>{ch}</span>
            );
          })}
        </div>
      ))}
    </AbsoluteFill>
  );
};

/** Slammed rubber stamp (e.g. SOTILDI). */
export const Stamp: React.FC<{text: string; at: number; until: number; y: number; color?: string; size?: number; rot?: number}> = ({text, at, until, y, color = RED, size = 120, rot = -8}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <StampInner {...{text, y, color, size, rot}} />
  </Sequence>
);
const StampInner: React.FC<any> = ({text, y, color, size, rot}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 9, stiffness: 260, mass: 0.7}});
  const sc = interpolate(s, [0, 1], [2.6, 1]);
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{
        fontFamily: ANTON, fontSize: size, color, padding: '6px 34px', border: `10px solid ${color}`, borderRadius: 18,
        transform: `rotate(${rot}deg) scale(${sc})`, opacity: Math.min(1, s * 2), background: 'rgba(0,0,0,0.35)',
        letterSpacing: 6, boxShadow: `0 0 50px ${color}66`, textShadow: '0 4px 0 rgba(0,0,0,0.5)',
      }}>{text}</div>
    </AbsoluteFill>
  );
};

/** Pill label (lower-third style callout). */
export const Pill: React.FC<{text: string; at: number; until: number; x?: number | string; y: number; bg?: string; color?: string; size?: number; from?: 'left' | 'right'}> = ({text, at, until, x = '50%', y, bg = YELLOW, color = '#111', size = 54, from = 'left'}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <PillInner {...{text, x, y, bg, color, size, from}} dur={f(until) - f(at)} />
  </Sequence>
);
const PillInner: React.FC<any> = ({text, x, y, bg, color, size, from, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 14, stiffness: 200}});
  const out = interpolate(frame, [dur - 5, dur], [1, 0], clamp);
  const dir = from === 'left' ? -1 : 1;
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, 0) translateX(${(1 - s) * 300 * dir}px)`, opacity: Math.min(s * 1.5, out)}}>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: size, color, background: bg, padding: '10px 28px', borderRadius: 14, whiteSpace: 'nowrap', boxShadow: '0 10px 30px rgba(0,0,0,0.45)', textTransform: 'uppercase'}}>{text}</div>
    </div>
  );
};

/** Animated number counter: $0 -> value. */
export const Counter: React.FC<{at: number; until: number; to: number; y: number; dur?: number}> = ({at, until, to, y, dur = 1.1}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <CounterInner to={to} y={y} dur={f(dur)} />
  </Sequence>
);
const CounterInner: React.FC<any> = ({to, y, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.7, 0.2, 1)});
  const val = Math.round(to * p);
  const pop = spring({frame: frame - dur, fps, config: {damping: 8, stiffness: 300}});
  const sc = 1 + (frame >= dur ? 0.12 * (1 - pop) + 0.0 : 0) + (frame < 6 ? (6 - frame) * 0.04 : 0);
  const str = '$' + val.toLocaleString('en-US').replace(/,/g, ' ');
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{fontFamily: ANTON, fontSize: 150, transform: `scale(${sc})`, fontVariantNumeric: 'tabular-nums',
        backgroundImage: 'linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        filter: 'drop-shadow(0 8px 0 rgba(0,0,0,0.6)) drop-shadow(0 0 40px rgba(61,255,138,0.55))'}}>{str}</div>
    </AbsoluteFill>
  );
};

/** Night clock: hands spin from 18:00 to 03:00. */
export const NightClock: React.FC<{at: number; until: number; y: number}> = ({at, until, y}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <ClockInner y={y} dur={f(until) - f(at)} />
  </Sequence>
);
const ClockInner: React.FC<any> = ({y, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 14}});
  const hoursPassed = interpolate(frame, [4, dur - 20], [0, 9], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const h = 18 + hoursPassed;
  const hourDeg = (h % 12) * 30;
  const minDeg = hoursPassed * 360;
  const hh = Math.floor(h) % 24;
  const label = `${String(hh).padStart(2, '0')}:${String(Math.floor((h % 1) * 60)).padStart(2, '0')}`;
  const out = interpolate(frame, [dur - 6, dur], [1, 0], clamp);
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', opacity: out, transform: `scale(${s})`}}>
      <svg width="360" height="360" viewBox="-180 -180 360 360">
        <circle r="165" fill="rgba(10,16,40,0.65)" stroke="white" strokeWidth="8" />
        <circle r="165" fill="none" stroke={CYAN} strokeWidth="8" strokeDasharray={`${(hoursPassed / 9) * 1036} 1036`} transform="rotate(-90)" />
        {Array.from({length: 12}).map((_, i) => (
          <line key={i} x1="0" y1="-140" x2="0" y2={i % 3 === 0 ? -115 : -127} stroke="white" strokeWidth={i % 3 === 0 ? 8 : 4} transform={`rotate(${i * 30})`} />
        ))}
        <line x1="0" y1="10" x2="0" y2="-80" stroke="white" strokeWidth="12" strokeLinecap="round" transform={`rotate(${hourDeg})`} />
        <line x1="0" y1="14" x2="0" y2="-120" stroke={YELLOW} strokeWidth="6" strokeLinecap="round" transform={`rotate(${minDeg})`} />
        <circle r="10" fill={YELLOW} />
      </svg>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 70, color: 'white', marginTop: 10, textShadow: txtShadow, fontVariantNumeric: 'tabular-nums'}}>
        <span style={{color: CYAN}}>☾ </span>{label}
      </div>
    </AbsoluteFill>
  );
};

/** Slot-machine year roll: 2026 -> 1990 */
export const YearRoll: React.FC<{at: number; until: number; y: number; from?: number; to?: number; suffix?: string}> = ({at, until, y, from = 2026, to = 1990, suffix = '-YILLAR'}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <YearInner {...{y, from, to, suffix}} dur={f(until) - f(at)} />
  </Sequence>
);
const YearInner: React.FC<any> = ({y, from, to, suffix, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = interpolate(frame, [0, 22], [0, 1], {...clamp, easing: Easing.bezier(0.1, 0.8, 0.2, 1)});
  const val = Math.round(from + (to - from) * p);
  const settle = spring({frame: frame - 22, fps, config: {damping: 7, stiffness: 300}});
  const rgb = frame < 24 ? 8 : 3 * (1 - settle);
  const out = interpolate(frame, [dur - 6, dur], [1, 0], clamp);
  const sty: React.CSSProperties = {fontFamily: ANTON, fontSize: 250, lineHeight: 1, letterSpacing: 4};
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', opacity: out}}>
      <div style={{position: 'relative', transform: `scale(${1 + 0.08 * (1 - settle) * (frame > 22 ? 1 : 0)})`}}>
        <div style={{...sty, color: '#ff2a6d', position: 'absolute', left: -rgb, top: 0, mixBlendMode: 'screen'}}>{val}</div>
        <div style={{...sty, color: '#05d9e8', position: 'absolute', left: rgb, top: 0, mixBlendMode: 'screen'}}>{val}</div>
        <div style={{...sty, color: 'white', position: 'relative', textShadow: '0 0 30px rgba(5,217,232,0.6)'}}>{val}</div>
      </div>
      <div style={{fontFamily: ANTON, fontSize: 110, color: YELLOW, opacity: interpolate(frame, [20, 28], [0, 1], clamp), letterSpacing: 8, textShadow: txtShadow}}>{suffix}</div>
    </AbsoluteFill>
  );
};

/** CRT scanlines overlay */
export const Scanlines: React.FC<{opacity?: number}> = ({opacity = 0.25}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity, pointerEvents: 'none', backgroundImage: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.9) 0px, rgba(0,0,0,0.9) 2px, transparent 2px, transparent 5px)', backgroundPosition: `0 ${frame * 2}px`}} />
  );
};

/** 90s-style browser window that "loads" zip2. */
export const RetroBrowser: React.FC<{at: number; until: number; y: number; stampAt: number}> = ({at, until, y, stampAt}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <BrowserInner y={y} dur={f(until) - f(at)} stamp={f(stampAt) - f(at)} />
  </Sequence>
);
const BrowserInner: React.FC<any> = ({y, dur, stamp}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 13, stiffness: 160}});
  const url = 'http://www.zip2.com';
  const typed = url.slice(0, Math.floor(interpolate(frame, [4, 18], [0, url.length], clamp)));
  const load = interpolate(frame, [16, 40], [0, 1], clamp);
  const logo = spring({frame: frame - 14, fps, config: {damping: 10, stiffness: 200}});
  const out = interpolate(frame, [dur - 6, dur], [1, 0], clamp);
  const st = spring({frame: frame - stamp, fps, config: {damping: 9, stiffness: 260}});
  const bevel = {borderTop: '4px solid #fff', borderLeft: '4px solid #fff', borderRight: '4px solid #404040', borderBottom: '4px solid #404040'};
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', opacity: out}}>
      <div style={{width: 900, background: '#c0c0c0', ...bevel, transform: `perspective(1400px) rotateX(${(1 - s) * 40}deg) scale(${0.6 + 0.4 * s})`, boxShadow: '0 40px 80px rgba(0,0,0,0.6)'}}>
        <div style={{background: 'linear-gradient(90deg,#000080,#1084d0)', color: 'white', fontFamily: MONT, fontWeight: 800, fontSize: 34, padding: '8px 14px', display: 'flex', justifyContent: 'space-between'}}>
          <span>Zip2 — Web Browser</span><span>_ □ ✕</span>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', fontFamily: 'monospace', fontSize: 34}}>
          <span style={{fontFamily: MONT, fontWeight: 800}}>Address:</span>
          <div style={{flex: 1, background: 'white', padding: '6px 10px', borderTop: '3px solid #404040', borderLeft: '3px solid #404040'}}>{typed}<span style={{opacity: frame % 16 < 8 ? 1 : 0}}>|</span></div>
        </div>
        <div style={{margin: '0 14px 14px', background: 'white', height: 430, borderTop: '3px solid #404040', borderLeft: '3px solid #404040', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden'}}>
          <div style={{fontFamily: ANTON, fontSize: 200, color: '#1a1a6e', transform: `scale(${logo})`, letterSpacing: 4}}>
            Zip<span style={{color: '#e8202a'}}>2</span>
          </div>
          <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 40, color: '#333', opacity: logo, letterSpacing: 3, marginBottom: 40}}>INTERNET KOMPANIYASI</div>
          <div style={{position: 'absolute', bottom: 16, left: 30, right: 30, height: 18, border: '3px solid #808080'}}>
            <div style={{width: `${load * 100}%`, height: '100%', background: 'repeating-linear-gradient(90deg,#000080 0 22px,transparent 22px 28px)'}} />
          </div>
          {frame >= stamp && (
            <div style={{position: 'absolute', fontFamily: ANTON, fontSize: 92, color: RED, border: `9px solid ${RED}`, borderRadius: 14, padding: '0 22px', transform: `rotate(-10deg) scale(${interpolate(st, [0, 1], [2.4, 1])})`, opacity: Math.min(1, st * 2), background: 'rgba(255,255,255,0.75)'}}>TASHKIL QILINDI</div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Floating Z z z for sleeping */
export const Zzz: React.FC<{at: number; until: number; x: number; y: number}> = ({at, until, x, y}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <ZInner x={x} y={y} />
  </Sequence>
);
const ZInner: React.FC<any> = ({x, y}) => {
  const frame = useCurrentFrame();
  return (
    <>
      {[0, 1, 2, 3].map((i) => {
        const t = ((frame + i * 10) % 40) / 40;
        return (
          <div key={i} style={{position: 'absolute', left: x + t * 160 + i * 10, top: y - t * 260, fontFamily: ANTON, fontSize: 70 + i * 20, color: 'white', opacity: interpolate(t, [0, 0.2, 0.8, 1], [0, 1, 1, 0]), transform: `rotate(${-15 + t * 20}deg)`, textShadow: txtShadow}}>Z</div>
        );
      })}
    </>
  );
};

/** Radial speed lines */
export const SpeedLines: React.FC<{opacity?: number}> = ({opacity = 0.5}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity, mixBlendMode: 'screen'}}>
      <svg width="1080" height="1920" viewBox="-540 -960 1080 1920">
        {Array.from({length: 60}).map((_, i) => {
          const a = random(`a${i}`) * Math.PI * 2;
          const r0 = 250 + ((random(`r${i}`) * 900 + frame * 70) % 900);
          const len = 120 + random(`l${i}`) * 200;
          return <line key={i} x1={Math.cos(a) * r0} y1={Math.sin(a) * r0} x2={Math.cos(a) * (r0 + len)} y2={Math.sin(a) * (r0 + len)} stroke="white" strokeWidth={2 + random(`w${i}`) * 4} strokeLinecap="round" opacity={0.7} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Company card that slides in (timeline). */
export const CompanyCard: React.FC<{at: number; until: number; y: number; title: string; color: string; src: string; video?: boolean; startFrom?: number; idx: number; activeUntil: number}> = ({at, until, y, title, color, src, video, startFrom = 0, idx, activeUntil}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <CardInner {...{y, title, color, src, video, startFrom, idx}} dur={f(until) - f(at)} active={f(activeUntil) - f(at)} />
  </Sequence>
);
const CardInner: React.FC<any> = ({y, title, color, src, video, startFrom, idx, dur, active}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 15, stiffness: 170}});
  const dir = idx % 2 === 0 ? -1 : 1;
  const isActive = frame < active;
  const out = interpolate(frame, [dur - 6, dur], [1, 0], clamp);
  const zoom = interpolate(frame, [0, dur], [1.05, 1.2]);
  return (
    <div style={{position: 'absolute', left: 70, top: y, width: 940, height: 400, transform: `translateX(${(1 - s) * 1100 * dir}px) scale(${isActive ? 1.0 : 0.94})`, opacity: out, borderRadius: 30, overflow: 'hidden', boxShadow: isActive ? `0 0 0 6px ${color}, 0 0 60px ${color}aa` : '0 0 0 3px rgba(255,255,255,0.4)', transition: 'none'}}>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${zoom})`, filter: isActive ? 'none' : 'brightness(0.6) saturate(0.7)'}}>
        {video ? <OffthreadVideo src={staticFile(src)} startFrom={Math.round(startFrom * FPS)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          : <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
      </div>
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(90deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.1) 65%)'}} />
      <div style={{position: 'absolute', left: 40, bottom: 34, fontFamily: ANTON, fontSize: 120, color: 'white', letterSpacing: 3, textShadow: txtShadow}}>{title}</div>
      <div style={{position: 'absolute', left: 44, top: 30, width: 70, height: 10, background: color, borderRadius: 6}} />
    </div>
  );
};

/** Top progress bar (retention cue). */
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left: 0, top: 0, height: 10, width: `${(frame / durationInFrames) * 100}%`, background: `linear-gradient(90deg, ${YELLOW}, ${GREEN})`, boxShadow: `0 0 18px ${YELLOW}`}} />
  );
};

/** Down-arrow CTA */
export const CTA: React.FC<{at: number; until: number; y: number; text: string}> = ({at, until, y, text}) => (
  <Sequence from={f(at)} durationInFrames={f(until) - f(at)} layout="none">
    <CTAInner y={y} text={text} />
  </Sequence>
);
const CTAInner: React.FC<any> = ({y, text}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 12}});
  const bob = Math.sin(frame / 4) * 8;
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', transform: `scale(${s})`}}>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 50, color: '#111', background: 'white', padding: '14px 34px', borderRadius: 60, boxShadow: '0 10px 30px rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', gap: 16}}>
        {text}
        <svg width="44" height="44" viewBox="0 0 24 24" style={{transform: `translateY(${bob}px)`}}><path d="M12 3v15m0 0l-6-6m6 6l6-6" stroke="#111" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
    </AbsoluteFill>
  );
};
