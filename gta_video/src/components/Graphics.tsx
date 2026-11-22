import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ANTON, C, MONT, accent, useLayout} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ---------- Kinetic headline: lines of words, staggered spring in, motion-blur style skew ----------
export const Kinetic: React.FC<{
  lines: string[]; // use *word* to accent a word
  color?: string;
  top?: number;
  size?: number;
  delay?: number;
  align?: 'center' | 'left';
  dur?: number;
}> = ({lines, color, top = 360, size = 150, delay = 0, align = 'center', dur}) => {
  const frame = useCurrentFrame() - delay;
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const {land} = useLayout();
  let idx = 0;
  const exit = dur ? interpolate(frame, [dur - delay - 8, dur - delay], [1, 0], clamp) : 1;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={land ? {position: 'absolute', top: 0, bottom: 0, left: 140, right: 140, display: 'flex', flexDirection: 'column', justifyContent: 'center', textAlign: align, opacity: exit} : {position: 'absolute', top, left: 60, right: 60, textAlign: align, opacity: exit}}>
        {lines.map((line, li) => (
          <div key={li} style={{display: 'block', lineHeight: 0.98, marginBottom: 10}}>
            {line.split(' ').map((raw, wi) => {
              const i = idx++;
              const isAcc = raw.startsWith('*');
              const word = raw.replace(/\*/g, '');
              const s = spring({frame: frame - i * 3, fps, config: {damping: 13, stiffness: 180, mass: 0.7}});
              const blur = interpolate(s, [0, 0.7, 1], [14, 2, 0], clamp);
              return (
                <span
                  key={wi}
                  style={{
                    display: 'inline-block',
                    marginRight: '0.22em',
                    fontFamily: ANTON,
                    fontSize: size,
                    textTransform: 'uppercase',
                    color: isAcc ? ac : C.white,
                    filter: `blur(${blur}px)`,
                    opacity: interpolate(s, [0, 0.4], [0, 1], clamp),
                    transform: `translateY(${interpolate(s, [0, 1], [90, 0])}px) skewX(${interpolate(s, [0, 1], [-14, 0])}deg) scale(${interpolate(s, [0, 1], [1.25, 1])})`,
                    textShadow: isAcc ? `0 0 40px ${ac}66, 0 10px 30px rgba(0,0,0,.8)` : '0 10px 30px rgba(0,0,0,.85)',
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Animated number counter ----------
export const Counter: React.FC<{
  to: number;
  from?: number;
  prefix?: string;
  suffix?: string;
  label?: string;
  sub?: string;
  color?: string;
  decimals?: number;
  top?: number;
  delay?: number;
  countDur?: number;
}> = ({to, from = 0, prefix = '', suffix = '', label, sub, color, decimals = 0, top = 420, delay = 0, countDur = 45}) => {
  const frame = useCurrentFrame() - delay;
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const p = interpolate(frame, [0, countDur], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const v = from + (to - from) * p;
  const txt = v.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals}).replace(/,/g, ' ');
  const s = spring({frame, fps, config: {damping: 12, stiffness: 160}});
  const {land, H} = useLayout();
  if (land) top = H / 2 - 200;
  const done = spring({frame: frame - countDur, fps, config: {damping: 8, stiffness: 260}});
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 40, right: 40, textAlign: 'center', transform: `scale(${interpolate(s, [0, 1], [0.6, 1]) + done * 0.06 - (frame > countDur + 8 ? 0.06 * Math.min(1, (frame - countDur - 8) / 8) : 0)})`, opacity: s}}>
        {label && (
          <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 46, color: C.white, letterSpacing: 6, textTransform: 'uppercase', marginBottom: 6, textShadow: '0 4px 20px #000'}}>
            {label}
          </div>
        )}
        <div
          style={{
            fontFamily: ANTON,
            fontSize: txt.length > 9 ? 150 : 200,
            color: ac,
            lineHeight: 1,
            textShadow: `0 0 60px ${ac}55, 0 12px 40px rgba(0,0,0,.9)`,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {prefix}
          {txt}
          {suffix}
        </div>
        {sub && (
          <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 52, color: C.white, marginTop: 14, textTransform: 'uppercase', textShadow: '0 4px 20px #000'}}>
            {sub}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Year stamp with timeline ruler ----------
export const YearStamp: React.FC<{year: number; label?: string; top?: number; color?: string; prev?: number}> = ({year, label, top = 330, color, prev}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const s = spring({frame, fps, config: {damping: 14, stiffness: 140}});
  const {land, H} = useLayout();
  if (land) top = H / 2 - 240;
  const start = prev ?? year - 6;
  const shown = Math.round(interpolate(frame, [0, 22], [start, year], {...clamp, easing: Easing.out(Easing.quad)}));
  const ticks = Array.from({length: 31}, (_, i) => i);
  const offset = interpolate(frame, [0, 30], [260, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 0, right: 0, textAlign: 'center', opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 260, color: C.white, lineHeight: 1, letterSpacing: 4, textShadow: `0 0 50px ${ac}44, 0 16px 50px rgba(0,0,0,.9)`, transform: `scale(${interpolate(s, [0, 1], [1.4, 1])})`}}>
          {shown}
        </div>
        <div style={{position: 'relative', height: 70, marginTop: 10, overflow: 'hidden', maskImage: 'linear-gradient(90deg, transparent, #000 25%, #000 75%, transparent)'}}>
          <div style={{position: 'absolute', left: '50%', top: 0, display: 'flex', gap: 26, transform: `translateX(${offset - 15 * 30}px)`}}>
            {ticks.map((i) => (
              <div key={i} style={{width: 4, height: i % 5 === 0 ? 56 : 26, background: i === 15 ? ac : 'rgba(255,255,255,.55)', borderRadius: 2}} />
            ))}
          </div>
        </div>
        {label && (
          <div style={{display: 'inline-block', marginTop: 18, padding: '10px 26px', background: ac, color: '#000', fontFamily: MONT, fontWeight: 900, fontSize: 44, textTransform: 'uppercase', borderRadius: 10, transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`}}>
            {label}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Chapter card ----------
export const Chapter: React.FC<{num: string; title: string; color?: string}> = ({num, title, color}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const s = spring({frame, fps, config: {damping: 16, stiffness: 120}});
  const bar = interpolate(frame, [4, 24], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', pointerEvents: 'none'}}>
      <div style={{marginTop: useLayout().land ? -60 : -260, textAlign: 'center'}}>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 40, letterSpacing: 18, color: ac, opacity: s, textTransform: 'uppercase'}}>{num}</div>
        <div style={{width: 600 * bar, height: 6, background: ac, margin: '22px auto', boxShadow: `0 0 30px ${ac}`}} />
        <div style={{fontFamily: ANTON, fontSize: 120, color: C.white, textTransform: 'uppercase', lineHeight: 1, padding: '0 60px', transform: `translateY(${interpolate(s, [0, 1], [60, 0])}px)`, opacity: s, textShadow: '0 12px 40px #000'}}>
          {title}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- Callout label (lower third / tag) ----------
export const Callout: React.FC<{title: string; sub?: string; top?: number; color?: string; delay?: number}> = ({title, sub, top = 250, color, delay = 0}) => {
  const frame = useCurrentFrame() - delay;
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const s = spring({frame, fps, config: {damping: 15, stiffness: 170}});
  const w = interpolate(frame, [0, 14], [0, 100], {...clamp, easing: Easing.out(Easing.cubic)});
  const {land} = useLayout();
  return (
    <div style={{position: 'absolute', ...(land ? {bottom: 110, left: 110} : {top, left: 70}), pointerEvents: 'none', opacity: frame < 0 ? 0 : 1}}>
      <div style={{clipPath: `inset(0 ${100 - w}% 0 0)`, background: ac, padding: '14px 28px', borderRadius: 8, display: 'inline-block'}}>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 52, color: '#000', textTransform: 'uppercase', letterSpacing: -0.5}}>{title}</div>
      </div>
      {sub && (
        <div style={{marginTop: 10, fontFamily: MONT, fontWeight: 700, fontSize: 36, color: C.white, opacity: s, transform: `translateX(${interpolate(s, [0, 1], [-30, 0])}px)`, textShadow: '0 4px 16px #000'}}>
          {sub}
        </div>
      )}
    </div>
  );
};

// ---------- Portrait card (person) ----------
export const Portrait: React.FC<{src: string; name: string; role?: string; color?: string; top?: number}> = ({src, name, role, color, top = 300}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const s = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const z = interpolate(frame, [0, 200], [1.05, 1.18], clamp);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 140, width: 800, height: 760, borderRadius: 30, overflow: 'hidden', border: `6px solid ${ac}`, boxShadow: `0 30px 90px rgba(0,0,0,.8), 0 0 60px ${ac}44`, transform: `translateY(${interpolate(s, [0, 1], [120, 0])}px) rotate(${interpolate(s, [0, 1], [6, -1.5])}deg)`, opacity: s}}>
        <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 25%', transform: `scale(${z})`, filter: 'contrast(1.08) saturate(1.05)'}} />
      </div>
      <div style={{position: 'absolute', top: top + 700, left: 110, transform: `translateX(${interpolate(s, [0, 1], [-80, 0])}px)`, opacity: s}}>
        <div style={{display: 'inline-block', background: '#000', padding: '12px 26px', borderLeft: `10px solid ${ac}`}}>
          <div style={{fontFamily: ANTON, fontSize: 72, color: C.white, textTransform: 'uppercase', lineHeight: 1}}>{name}</div>
          {role && <div style={{fontFamily: MONT, fontWeight: 700, fontSize: 32, color: ac, marginTop: 6}}>{role}</div>}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- Bar chart ----------
export const Bars: React.FC<{title: string; items: {label: string; value: number; display?: string}[]; color?: string; top?: number}> = ({title, items, color, top = 260}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const max = Math.max(...items.map((i) => i.value));
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 70, right: 70}}>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 50, color: C.white, textTransform: 'uppercase', marginBottom: 30, textShadow: '0 4px 20px #000'}}>{title}</div>
        {items.map((it, i) => {
          const s = spring({frame: frame - 6 - i * 6, fps, config: {damping: 18, stiffness: 90}});
          const last = i === items.length - 1;
          return (
            <div key={i} style={{marginBottom: 22}}>
              <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 34, color: C.muted, marginBottom: 6, opacity: s}}>{it.label}</div>
              <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
                <div style={{height: 54, width: `${(it.value / max) * 76 * s}%`, background: last ? ac : 'rgba(255,255,255,.85)', borderRadius: 8, boxShadow: last ? `0 0 40px ${ac}88` : 'none'}} />
                <div style={{fontFamily: ANTON, fontSize: 52, color: last ? ac : C.white, opacity: s}}>{it.display ?? it.value}</div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Bullet list with check icons ----------
export const List: React.FC<{title?: string; items: string[]; color?: string; top?: number; stagger?: number}> = ({title, items, color, top = 300, stagger = 12}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top, left: 80, right: 80}}>
        {title && <div style={{fontFamily: ANTON, fontSize: 96, color: C.white, textTransform: 'uppercase', marginBottom: 30, textShadow: '0 8px 30px #000'}}>{title}</div>}
        {items.map((t, i) => {
          const s = spring({frame: frame - i * stagger, fps, config: {damping: 14, stiffness: 160}});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24, opacity: s, transform: `translateX(${interpolate(s, [0, 1], [-120, 0])}px)`}}>
              <div style={{width: 70, height: 70, borderRadius: 16, background: ac, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: `0 0 30px ${ac}66`}}>
                <svg width="40" height="40" viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7" stroke="#000" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 56, color: C.white, textTransform: 'uppercase', textShadow: '0 6px 24px #000', lineHeight: 1.05}}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Quote card ----------
export const Quote: React.FC<{text: string; who?: string; color?: string; top?: number}> = ({text, who, color, top = 300}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ac = accent(color);
  const s = spring({frame, fps, config: {damping: 15, stiffness: 120}});
  const chars = Math.floor(interpolate(frame, [6, 6 + text.length * 0.9], [0, text.length], clamp));
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', ...(useLayout().land ? {top: 220, left: 360, right: 360} : {top, left: 80, right: 80}), padding: '50px 50px 40px', background: 'rgba(8,8,14,.82)', borderRadius: 30, border: '2px solid rgba(255,255,255,.12)', boxShadow: '0 30px 80px rgba(0,0,0,.6)', transform: `scale(${interpolate(s, [0, 1], [0.9, 1])})`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 200, color: ac, lineHeight: 0.6, height: 90}}>“</div>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 58, color: C.white, lineHeight: 1.2}}>
          {text.slice(0, chars)}
          <span style={{opacity: frame % 20 < 10 ? 1 : 0, color: ac}}>|</span>
        </div>
        {who && <div style={{fontFamily: MONT, fontWeight: 700, fontSize: 34, color: ac, marginTop: 26, textTransform: 'uppercase', letterSpacing: 3}}>— {who}</div>}
      </div>
    </AbsoluteFill>
  );
};

// ---------- Glitch wrapper (RGB split for a few frames at start) ----------
export const Glitch: React.FC<{children: React.ReactNode; frames?: number; seed?: number}> = ({children, frames = 8, seed = 1}) => {
  const frame = useCurrentFrame();
  if (frame > frames) return <>{children}</>;
  const amt = interpolate(frame, [0, frames], [26, 0]);
  const dx = (random(seed + frame) - 0.5) * amt;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{transform: `translateX(${dx}px)`, mixBlendMode: 'screen', filter: 'url(#r)'}}>{children}</AbsoluteFill>
      <AbsoluteFill style={{transform: `translateX(${-dx}px)`, opacity: 0.6, mixBlendMode: 'screen'}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- Camera shake wrapper ----------
export const Shake: React.FC<{children: React.ReactNode; amount?: number; frames?: number}> = ({children, amount = 18, frames = 14}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, frames], [amount, 0], clamp);
  const x = (random(`x${frame}`) - 0.5) * a;
  const y = (random(`y${frame}`) - 0.5) * a;
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px) rotate(${(random(`r${frame}`) - 0.5) * a * 0.05}deg)`}}>{children}</AbsoluteFill>;
};
