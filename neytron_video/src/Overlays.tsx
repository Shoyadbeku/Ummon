import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import {C, HEAD, BODY, ease, pop, textStroke, sec} from './theme';
import type {Shot} from './Main';

// Kinetic headline: words slam in one by one
export const Kinetic: React.FC<{text: string; size?: number; delay?: number; color?: string; accent?: string[]; stagger?: number; width?: number}> = ({
  text, size = 96, delay = 0, color = '#fff', accent = [], stagger = 3, width = 940,
}) => {
  const f = useCurrentFrame();
  const words = text.split(' ');
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: `0px ${size * 0.26}px`, width}}>
      {words.map((w, i) => {
        const p = pop(f, delay + i * stagger, 11, 170, 0.7);
        const hi = accent.some((a) => w.toUpperCase().startsWith(a));
        return (
          <span
            key={i}
            style={{
              fontFamily: HEAD, fontWeight: 900, fontSize: size, lineHeight: 1.04, color: hi ? C.gold : color,
              display: 'inline-block', transform: `translateY(${(1 - p) * 60}px) scale(${0.6 + 0.4 * p})`,
              opacity: Math.min(1, p * 1.5), letterSpacing: -1, textShadow: '0 10px 40px rgba(0,0,0,0.7)',
              ...textStroke(4, 'rgba(0,0,0,0.6)'),
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

const Label: React.FC<{text: string; sub?: string}> = ({text, sub}) => {
  const f = useCurrentFrame();
  const bar = ease(f, 2, 14);
  const txt = ease(f, 6, 20);
  return (
    <div style={{position: 'absolute', top: 300, left: 70, right: 70, display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
      <div style={{display: 'flex', alignItems: 'stretch'}}>
        <div style={{width: 12, background: C.gold, transform: `scaleY(${bar})`, transformOrigin: 'top', borderRadius: 3}} />
        <div style={{overflow: 'hidden', marginLeft: 18}}>
          <div
            style={{
              fontFamily: HEAD, fontWeight: 900, fontSize: text.length > 22 ? 54 : 70, color: '#fff', lineHeight: 1.05,
              transform: `translateX(${(1 - txt) * -110}%)`, maxWidth: 900, textShadow: '0 8px 30px rgba(0,0,0,0.75)',
              background: 'rgba(6,8,14,0.55)', padding: '10px 22px', borderRadius: 8,
            }}
          >
            {text}
          </div>
        </div>
      </div>
      {sub ? (
        <div
          style={{
            marginTop: 12, marginLeft: 30, fontFamily: BODY, fontWeight: 700, fontSize: 34, color: C.gold,
            opacity: ease(f, 14, 26), transform: `translateY(${(1 - ease(f, 14, 26)) * 20}px)`, textTransform: 'uppercase', letterSpacing: 2,
            textShadow: '0 4px 16px rgba(0,0,0,0.9)',
          }}
        >
          {sub}
        </div>
      ) : null}
    </div>
  );
};

const Arrow: React.FC<{dir: string; size: number; color: string}> = ({dir, size, color}) => {
  const f = useCurrentFrame();
  const bob = Math.sin(f / 5) * 8;
  const rot = dir === 'up' ? -90 : dir === 'down' ? 90 : 0;
  if (dir === 'updown') {
    return (
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 0.8}}>
        <svg width={size} height={size * 0.6} viewBox="0 0 100 60" style={{transform: `translateY(${-Math.abs(bob)}px)`}}><path d="M50 0 L100 60 L0 60 Z" fill={C.green} /></svg>
        <svg width={size} height={size * 0.6} viewBox="0 0 100 60" style={{marginTop: 8, transform: `translateY(${Math.abs(bob)}px)`}}><path d="M0 0 L100 0 L50 60 Z" fill={C.red} /></svg>
      </div>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" style={{transform: `rotate(${rot}deg) translateX(${bob}px)`}}>
      <path d="M10 40 H60 V18 L95 50 L60 82 V60 H10 Z" fill={color} />
    </svg>
  );
};

const Stat: React.FC<{text: string; dir: string}> = ({text, dir}) => {
  const f = useCurrentFrame();
  const p = pop(f, 2, 12, 150);
  const color = dir === 'up' ? C.red : dir === 'down' ? C.red : C.cyan;
  return (
    <div style={{position: 'absolute', top: 290, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 26, padding: '22px 40px', borderRadius: 26,
          background: 'rgba(8,10,16,0.72)', border: `3px solid ${color}`, transform: `scale(${0.5 + 0.5 * p})`, opacity: Math.min(1, p * 1.4),
          boxShadow: `0 0 60px ${color}55`,
        }}
      >
        <Arrow dir={dir} size={110} color={color} />
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: text.length > 18 ? 50 : 66, color: '#fff', maxWidth: 680, lineHeight: 1.05}}>{text}</div>
      </div>
    </div>
  );
};

const Stamp: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const p = pop(f, 4, 9, 260, 0.6);
  const shake = f >= 4 && f < 12 ? Math.sin(f * 3) * (12 - f) : 0;
  return (
    <AbsoluteFill style={{alignItems: 'center', top: -260, justifyContent: 'center', transform: `translateX(${shake}px)`}}>
      <div
        style={{
          transform: `rotate(-8deg) scale(${2.4 - 1.4 * p})`, opacity: Math.min(1, p * 2), border: `10px solid ${C.red}`, borderRadius: 18,
          padding: '14px 34px', fontFamily: HEAD, fontWeight: 900, fontSize: text.length > 14 ? 64 : 92, color: C.red, letterSpacing: 2,
          background: 'rgba(0,0,0,0.35)', textAlign: 'center', maxWidth: 900, lineHeight: 1.05, boxShadow: '0 0 0 4px rgba(255,61,61,0.25)',
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

const Breaking: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const a = ease(f, 0, 12);
  const b = ease(f, 8, 22);
  const blink = Math.floor(f / 10) % 2 === 0 ? 1 : 0.35;
  return (
    <div style={{position: 'absolute', top: 980, left: 40, right: 40}}>
      <div style={{display: 'inline-flex', alignItems: 'center', gap: 12, background: C.red, padding: '10px 20px', transform: `scaleX(${a})`, transformOrigin: 'left'}}>
        <div style={{width: 16, height: 16, borderRadius: 8, background: '#fff', opacity: blink}} />
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 34, color: '#fff', letterSpacing: 3}}>SO'NGGI XABAR</div>
      </div>
      <div style={{overflow: 'hidden'}}>
        <div style={{background: 'rgba(255,255,255,0.95)', padding: '16px 24px', transform: `translateY(${(1 - b) * -100}%)`}}>
          <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 46, color: '#0b0d14', lineHeight: 1.1}}>{text}</div>
        </div>
      </div>
    </div>
  );
};

const Notif: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const items = ['Bir davlat urush boshlagan', 'Dollar qimmatlashgan', 'Milliarder milliardlab dollar yo\'qotgan'];
  return (
    <div style={{position: 'absolute', top: 300, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 18}}>
      {items.map((it, i) => {
        const p = pop(f, i * 5, 13, 160);
        return (
          <div
            key={i}
            style={{
              display: 'flex', alignItems: 'center', gap: 20, padding: '20px 24px', borderRadius: 28,
              background: 'rgba(245,247,250,0.9)', transform: `translateY(${(1 - p) * -80}px) scale(${0.9 + 0.1 * p})`, opacity: p,
              boxShadow: '0 20px 50px rgba(0,0,0,0.4)',
            }}
          >
            <div style={{width: 64, height: 64, borderRadius: 16, background: i === 0 ? C.red : i === 1 ? '#1e9e57' : '#222', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, color: '#fff', fontFamily: HEAD, fontWeight: 900}}>
              {i === 0 ? '!' : i === 1 ? '$' : '↓'}
            </div>
            <div>
              <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 24, color: '#666', letterSpacing: 1}}>{text} · hozir</div>
              <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 34, color: '#111'}}>{it}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export const Hook: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const shake = f < 10 ? Math.sin(f * 2.7) * (10 - f) * 1.6 : 0;
  const line = ease(f, 10, 24);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -260, transform: `translate(${shake}px, ${-shake}px)`}}>
      <div style={{background: 'radial-gradient(closest-side, rgba(0,0,0,0.6), rgba(0,0,0,0))', padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <Kinetic text={text} size={120} stagger={2} accent={['KIM']} width={960} />
        <div style={{height: 12, width: 520, background: C.red, marginTop: 18, transform: `scaleX(${line})`, borderRadius: 6}} />
      </div>
    </AbsoluteFill>
  );
};

const Quote: React.FC<{text: string}> = ({text}) => {
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -280}}>
      <div style={{background: 'radial-gradient(closest-side, rgba(0,0,0,0.55), rgba(0,0,0,0))', padding: '40px 20px'}}>
        <Kinetic text={text} size={text.length > 28 ? 82 : 100} delay={2} accent={['KIM', 'EMAS', 'YANGI', 'MURAKKAB', 'BITTA', 'NEGA', 'MAXFIY']} />
      </div>
    </AbsoluteFill>
  );
};

const Big: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const p = pop(f, 2, 10, 120);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: -200}}>
      <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 520, color: 'transparent', WebkitTextStroke: `10px ${C.gold}`, transform: `scale(${0.4 + 0.6 * p})`, opacity: p, textShadow: `0 0 80px ${C.gold}66`}}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const Overlay: React.FC<{ov: NonNullable<Shot['overlay']>; shot: Shot}> = ({ov}) => {
  switch (ov.type) {
    case 'hook': return null; // rendered globally in Main
    case 'label': return <Label text={ov.text} sub={ov.extra} />;
    case 'stat': return <Stat text={ov.text} dir={ov.extra || 'up'} />;
    case 'stamp': return <Stamp text={ov.text} />;
    case 'quote': return <Quote text={ov.text} />;
    case 'breaking': return <Breaking text={ov.text} />;
    case 'notif': return <Notif text={ov.text} />;
    case 'big': return <Big text={ov.text} />;
    default: return null;
  }
};
