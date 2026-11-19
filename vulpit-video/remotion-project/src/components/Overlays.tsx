import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONT_SANS, FONT_SERIF, OverlayT, SB, VOICE_LVL, pick, ty} from '../data';
import {LightLeak} from './Effects';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const useOut = (dur: number, len = 10) => {
  const f = useCurrentFrame();
  return interpolate(f, [dur - len, dur], [1, 0], clamp);
};
const shadow = '0 6px 24px rgba(0,0,0,0.85), 0 2px 4px rgba(0,0,0,0.9)';
const greenGlow = (k = 1) => `0 0 ${30 * k}px rgba(108,240,160,0.75), 0 0 ${80 * k}px rgba(31,169,104,0.55), ${shadow}`;

/** Text that reveals through a moving mask from left to right. */
const MaskReveal: React.FC<{children: React.ReactNode; delay?: number; len?: number}> = ({children, delay = 0, len = 16}) => {
  const f = useCurrentFrame();
  const q = interpolate(f - delay, [0, len], [100, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  const y = interpolate(f - delay, [0, len], [24, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  return <div style={{clipPath: `inset(0 ${q}% 0 0)`, transform: `translateY(${y}px)`}}>{children}</div>;
};

const Impact: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f, fps, config: {damping: 9, stiffness: 160, mass: 0.8}});
  const scale = interpolate(sp, [0, 1], [2.6, 1]);
  const jx = f < 10 ? (random(`ix${f}`) - 0.5) * 16 : 0;
  const out = useOut(o.dur, 14);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: pick(-620, -400)}}>
      <div style={{position: 'relative', transform: `translateX(${jx}px) scale(${scale})`, opacity: Math.min(1, sp * 2) * out}}>
        {/* chromatic split ghost */}
        <div style={{position: 'absolute', inset: 0, fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 210, letterSpacing: 6, color: 'rgba(255,60,90,0.35)', transform: `translateX(${(1 - sp) * 18 + 3}px)`}}>{o.text}</div>
        <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 210, letterSpacing: 6, color: COLORS.green, textShadow: greenGlow(1 + (VOICE_LVL[o.from + f] ?? 0))}}>{o.text}</div>
      </div>
    </AbsoluteFill>
  );
};

const Counter: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [0, 32], [0, Number(o.text)], {...clamp, easing: Easing.out(Easing.cubic)}));
  const out = useOut(o.dur);
  const blur = interpolate(f, [0, 32], [6, 0], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-280), opacity: out}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 14, filter: `blur(${blur}px)`}}>
        <span style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 230, color: COLORS.white, textShadow: shadow, fontVariantNumeric: 'tabular-nums'}}>{n}</span>
        <span style={{fontFamily: FONT_SANS, fontWeight: 900, fontSize: 74, color: COLORS.gold, textShadow: shadow}}>{o.suffix}</span>
      </div>
      {o.sub ? (
        <MaskReveal delay={20}>
          <div style={{fontFamily: FONT_SANS, fontWeight: 800, fontSize: 40, letterSpacing: 14, color: COLORS.green, textShadow: shadow, marginTop: 4}}>{o.sub}</div>
        </MaskReveal>
      ) : null}
    </AbsoluteFill>
  );
};

const Word: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f, fps, config: {damping: 11, stiffness: 190}});
  const out = useOut(o.dur, 8);
  const y = pick(150, 70) + (o.pos ?? 0) * pick(125, 112);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center', opacity: Math.min(1, sp * 1.6) * out, transform: `scale(${interpolate(sp, [0, 1], [1.7, 1])})`}}>
      <span style={{fontFamily: FONT_SANS, fontWeight: 900, fontSize: 100, letterSpacing: -1, color: o.color === 'green' ? COLORS.green : COLORS.white, textShadow: o.color === 'green' ? greenGlow(0.8) : shadow}}>{o.text}</span>
    </div>
  );
};

const Title: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const [l1, l2, l3] = o.text.split('|');
  const ls = interpolate(f, [0, 60], [0.4, 0.1], {...clamp, easing: Easing.out(Easing.cubic)});
  const op = interpolate(f, [0, 14], [0, 1], clamp) * useOut(o.dur, 12);
  const sweep = interpolate(f, [8, 70], [-60, 160], clamp);
  const lineW = interpolate(f, [10, 45], [0, 520], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const grad = (base: string) => `linear-gradient(100deg, ${base} 0%, ${base} ${sweep - 20}%, #ffffff ${sweep - 6}%, #e9fff0 ${sweep}%, ${base} ${sweep + 12}%, ${base} 100%)`;
  const textStyle: React.CSSProperties = {
    fontFamily: FONT_SERIF, fontWeight: 900, letterSpacing: `${ls}em`, lineHeight: 1.0, textAlign: 'center',
    WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent',
  };
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: op, top: ty(-120)}}>
      <div style={{...textStyle, fontSize: 78, backgroundImage: grad('#f7f4ee'), filter: 'drop-shadow(0 6px 18px rgba(0,0,0,0.9))'}}>{l1}</div>
      <div style={{...textStyle, fontSize: 168, backgroundImage: grad('#8ff5b6'), filter: 'drop-shadow(0 0 30px rgba(108,240,160,0.55)) drop-shadow(0 6px 18px rgba(0,0,0,0.9))'}}>{l2}</div>
      <div style={{...textStyle, fontSize: 92, backgroundImage: grad('#f7f4ee'), filter: 'drop-shadow(0 6px 18px rgba(0,0,0,0.9))'}}>{l3}</div>
      <div style={{width: lineW, height: 3, background: 'linear-gradient(90deg, transparent, #6CF0A0, transparent)', margin: '26px 0 22px'}} />
      <MaskReveal delay={26}>
        <div style={{fontFamily: FONT_SANS, fontWeight: 800, fontSize: 30, letterSpacing: 7, color: COLORS.gold, textShadow: shadow}}>{o.sub}</div>
      </MaskReveal>
    </AbsoluteFill>
  );
};

const Title2: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const [l1, l2] = o.text.split('|');
  const op = interpolate(f, [0, 18], [0, 1], clamp) * useOut(o.dur, 16);
  const ls = interpolate(f, [0, o.dur], [0.32, 0.16], clamp);
  const blur = interpolate(f, [0, 18], [14, 0], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-330), opacity: op, filter: `blur(${blur}px)`}}>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 74, letterSpacing: `${ls * 0.6}em`, color: COLORS.green, textShadow: greenGlow(1.1)}}>{l1}</div>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 700, fontSize: 58, letterSpacing: `${ls}em`, color: COLORS.white, textShadow: shadow}}>{l2}</div>
    </AbsoluteFill>
  );
};

const Chapter: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 14);
  const lw = interpolate(f, [0, 22], [0, 90], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: pick(64, 90), top: pick(128, 60), opacity: out, display: 'flex', alignItems: 'center', gap: 20}}>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 44, color: COLORS.green, textShadow: greenGlow(0.4)}}>{o.num}</div>
      <div style={{width: lw, height: 2, background: COLORS.green}} />
      <MaskReveal delay={8}>
        <div style={{fontFamily: FONT_SANS, fontWeight: 800, fontSize: 34, letterSpacing: 8, color: COLORS.white, textShadow: shadow}}>{o.text}</div>
      </MaskReveal>
    </div>
  );
};

const Stamp: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 14);
  const chars = Math.floor(interpolate(f, [0, 16], [0, o.text.length], clamp));
  const caret = f < 40 && Math.floor(f / 6) % 2 === 0;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-300), opacity: out}}>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 150, letterSpacing: 18, color: COLORS.white, textShadow: shadow}}>
        {o.text.slice(0, chars)}<span style={{opacity: caret ? 1 : 0, color: COLORS.green}}>|</span>
      </div>
      <MaskReveal delay={18}>
        <div style={{display: 'flex', alignItems: 'center', gap: 16, fontFamily: FONT_SANS, fontWeight: 800, fontSize: 34, letterSpacing: 8, color: COLORS.gold, textShadow: shadow}}>
          <svg width="26" height="34" viewBox="0 0 24 32"><path d="M12 0C5.4 0 0 5.2 0 11.7 0 20.4 12 32 12 32s12-11.6 12-20.3C24 5.2 18.6 0 12 0zm0 16a4.5 4.5 0 110-9 4.5 4.5 0 010 9z" fill="#F3C969" /></svg>
          {o.sub}
        </div>
      </MaskReveal>
    </AbsoluteFill>
  );
};

const Name: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 12);
  const bar = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: pick(64, 90), top: pick(1250, 700), opacity: out, display: 'flex', gap: 18}}>
      <div style={{width: 6, height: 110 * bar, background: `linear-gradient(${COLORS.green}, ${COLORS.greenDeep})`, boxShadow: '0 0 14px rgba(108,240,160,0.7)'}} />
      <div>
        <MaskReveal delay={4}>
          <div style={{fontFamily: FONT_SANS, fontWeight: 900, fontSize: 50, color: COLORS.white, textShadow: shadow, letterSpacing: 1}}>{o.text}</div>
        </MaskReveal>
        <MaskReveal delay={12}>
          <div style={{fontFamily: FONT_SANS, fontWeight: 600, fontSize: 32, color: COLORS.gold, textShadow: shadow, marginTop: 4}}>{o.sub}</div>
        </MaskReveal>
      </div>
    </div>
  );
};

const Dates: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const [a, b] = o.text.split(' — ').map(Number);
  const out = useOut(o.dur, 14);
  const n1 = Math.round(interpolate(f, [0, 22], [1066, a], {...clamp, easing: Easing.out(Easing.cubic)}));
  const n2 = Math.round(interpolate(f, [10, 34], [a, b], {...clamp, easing: Easing.out(Easing.cubic)}));
  const lw = interpolate(f, [6, 30], [0, 120], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-320), opacity: out}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 26, fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 120, color: COLORS.white, textShadow: shadow, fontVariantNumeric: 'tabular-nums'}}>
        <span>{n1}</span>
        <span style={{width: lw, height: 4, background: COLORS.gold, display: 'inline-block'}} />
        <span style={{opacity: interpolate(f, [8, 14], [0, 1], clamp)}}>{n2}</span>
      </div>
      <MaskReveal delay={22}>
        <div style={{fontFamily: FONT_SANS, fontWeight: 800, fontSize: 36, letterSpacing: 10, color: COLORS.gold, textShadow: shadow}}>{o.sub}</div>
      </MaskReveal>
    </AbsoluteFill>
  );
};

const List: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const items = o.text.split('|');
  const out = useOut(o.dur, 10);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-300), opacity: out}}>
      <div style={{display: 'flex', gap: 34}}>
        {items.map((it, i) => {
          const t = o.times?.[i] ?? i * 10;
          const sp = spring({frame: f - t, fps, config: {damping: 12, stiffness: 200}});
          return (
            <div key={i} style={{fontFamily: FONT_SANS, fontWeight: 900, fontSize: 92, color: i === 2 ? COLORS.white : COLORS.gold, textShadow: shadow, opacity: f >= t ? Math.min(1, sp * 1.5) : 0, transform: `translateY(${(1 - sp) * 40}px) scale(${0.7 + 0.3 * sp})`}}>
              {it.replace(/'/g, 'ʻ')}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Quote: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const lines = o.text.split('|');
  const out = useOut(o.dur, 14);
  const words = lines.map((l) => l.split(' '));
  let k = 0;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-330), opacity: out}}>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 170, lineHeight: 0.6, color: COLORS.green, textShadow: greenGlow(0.6), opacity: interpolate(f, [0, 10], [0, 1], clamp)}}>“</div>
      {words.map((ws, li) => (
        <div key={li} style={{display: 'flex', gap: 22}}>
          {ws.map((w) => {
            const d = 4 + 6 * k++;
            return (
              <span key={w + d} style={{fontFamily: FONT_SERIF, fontWeight: 700, fontSize: 70, color: COLORS.white, textShadow: shadow, opacity: interpolate(f - d, [0, 10], [0, 1], clamp), filter: `blur(${interpolate(f - d, [0, 10], [8, 0], clamp)}px)`}}>
                {w}
              </span>
            );
          })}
        </div>
      ))}
    </AbsoluteFill>
  );
};

const Theory: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 14);
  const box = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: pick(64, 90), right: pick(64, 90), top: pick(160, 70), opacity: out}}>
      <div style={{display: 'inline-block', padding: '8px 18px', background: COLORS.green, color: COLORS.ink, fontFamily: FONT_SANS, fontWeight: 900, fontSize: 30, letterSpacing: 6, transform: `scaleX(${box})`, transformOrigin: 'left'}}>
        NAZARIYA № {o.num}
      </div>
      <MaskReveal delay={8}>
        <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 66, color: COLORS.white, textShadow: shadow, marginTop: 14, letterSpacing: 2}}>{o.text}</div>
      </MaskReveal>
    </div>
  );
};

const Term: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 12);
  const ls = interpolate(f, [0, o.dur], [0.3, 0.18], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-280), opacity: out}}>
      <MaskReveal len={20}>
        <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 130, letterSpacing: `${ls}em`, color: COLORS.green, textShadow: greenGlow(0.8)}}>{o.text}</div>
      </MaskReveal>
      <MaskReveal delay={14}>
        <div style={{fontFamily: FONT_SANS, fontWeight: 800, fontSize: 44, color: COLORS.white, textShadow: shadow}}>{o.sub}</div>
      </MaskReveal>
    </AbsoluteFill>
  );
};

const Route: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const out = useOut(o.dur, 12);
  const [a, b] = o.text.split(' → ');
  const p = interpolate(f, [8, 36], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-320), opacity: out}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 20, fontFamily: FONT_SANS, fontWeight: 900, fontSize: 58, color: COLORS.white, textShadow: shadow}}>
        <MaskReveal>{a}</MaskReveal>
        <svg width="190" height="40" viewBox="0 0 190 40">
          <path d="M5 20 Q 95 -6 175 20" stroke={COLORS.gold} strokeWidth="4" fill="none" strokeDasharray="200" strokeDashoffset={200 * (1 - p)} />
          <path d="M165 10 L180 20 L165 30" stroke={COLORS.gold} strokeWidth="4" fill="none" opacity={p > 0.9 ? 1 : 0} />
        </svg>
        <span style={{opacity: interpolate(f, [30, 40], [0, 1], clamp), color: COLORS.green}}>{b}</span>
      </div>
      <MaskReveal delay={30}>
        <div style={{fontFamily: FONT_SANS, fontWeight: 600, fontSize: 36, color: COLORS.gold, textShadow: shadow, marginTop: 6}}>({o.sub})</div>
      </MaskReveal>
    </AbsoluteFill>
  );
};

const CTA: React.FC<{o: OverlayT}> = ({o}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f, fps, config: {damping: 13, stiffness: 140}});
  const bellF = o.bell ?? 120;
  const sp2 = spring({frame: f - bellF + 20, fps, config: {damping: 12, stiffness: 160}});
  const ring = f >= bellF && f < bellF + 40 ? Math.sin((f - bellF) * 1.3) * 22 * Math.exp(-(f - bellF) / 14) : 0;
  const out = interpolate(f, [o.dur - 30, o.dur], [1, 0], clamp);
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', top: ty(-300), opacity: out}}>
      <div style={{fontFamily: FONT_SERIF, fontWeight: 900, fontSize: 132, color: COLORS.green, textShadow: greenGlow(1), transform: `scale(${interpolate(sp, [0, 1], [0.6, 1])})`, opacity: Math.min(1, sp * 1.5)}}>{o.text}</div>
      <div style={{marginTop: 30, display: 'flex', alignItems: 'center', gap: 24, opacity: f >= bellF - 20 ? Math.min(1, sp2 * 1.4) : 0, transform: `translateY(${(1 - sp2) * 40}px)`}}>
        <div style={{padding: '18px 40px', borderRadius: 18, background: '#E8322E', fontFamily: FONT_SANS, fontWeight: 900, fontSize: 46, color: '#fff', letterSpacing: 2, boxShadow: '0 10px 30px rgba(0,0,0,0.6)'}}>OBUNA BOʻLING</div>
        <svg width="78" height="78" viewBox="0 0 24 24" style={{transform: `rotate(${ring}deg)`, transformOrigin: '50% 10%', filter: 'drop-shadow(0 6px 14px rgba(0,0,0,0.8))'}}>
          <path fill="#F3C969" d="M12 22a2.5 2.5 0 002.45-2h-4.9A2.5 2.5 0 0012 22zm7-6V11a7 7 0 00-5.5-6.84V3.5a1.5 1.5 0 00-3 0v.66A7 7 0 005 11v5l-2 2v1h18v-1l-2-2z" />
        </svg>
      </div>
    </AbsoluteFill>
  );
};

const MAP: Record<string, React.FC<{o: OverlayT}>> = {
  impact: Impact, counter: Counter, word: Word, title: Title, title2: Title2, chapter: Chapter, stamp: Stamp, name: Name,
  dates: Dates, list: List, quote: Quote, theory: Theory, term: Term, route: Route, cta: CTA,
};

export const Overlays: React.FC = () => (
  <>
    {SB.overlays.map((o, i) => {
      const C = MAP[o.type];
      if (!C) return null;
      return (
        <Sequence key={i} from={o.from} durationInFrames={o.dur} name={`${o.type}: ${o.text}`} layout="none">
          <C o={o} />
          {o.type === 'title' || o.type === 'title2' ? <LightLeak dur={Math.min(o.dur, 70)} hue={o.type === 'title2' ? 'green' : 'warm'} /> : null}
        </Sequence>
      );
    })}
  </>
);
