import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing, random, delayRender, continueRender} from 'remotion';
import scenesData from '../public/scenes.json';
import wordsData from '../public/words.json';

const fontFamily = 'Mont';
const serif = 'Playfair';
if (typeof window !== 'undefined') {
  const handle = delayRender('fonts');
  const faces = [
    new FontFace('Mont', `url(${staticFile('fonts/montserrat-latin-600-normal.woff2')})`, {weight: '600'}),
    new FontFace('Mont', `url(${staticFile('fonts/montserrat-latin-900-normal.woff2')})`, {weight: '700 900'}),
    new FontFace('Playfair', `url(${staticFile('fonts/playfair-display-latin-700-italic.woff2')})`, {weight: '700', style: 'italic'}),
  ];
  Promise.all(faces.map((ff) => ff.load())).then((ls) => {ls.forEach((l) => document.fonts.add(l)); continueRender(handle);})
    .catch((e) => {console.error(e); continueRender(handle);});
}
export const FPS = 30;
const HOOK = scenesData.hook;
const GREEN = '#8CFF5A';
const VICTORY = HOOK + 39.2;
const f = (s: number) => Math.round(s * FPS);
const XF = 0.35; // crossfade seconds

type Scene = {start: number; end: number; img: string; motion: string; tag: string | null};

const KenBurns: React.FC<{scene: Scene; idx: number}> = ({scene, idx}) => {
  const frame = useCurrentFrame();
  const dur = f(scene.end - scene.start + XF);
  const p = interpolate(frame, [0, dur], [0, 1], {extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
  let scale = 1.12, x = 0, y = 0;
  switch (scene.motion) {
    case 'zoomIn': scale = 1.08 + 0.18 * p; break;
    case 'zoomOut': scale = 1.28 - 0.18 * p; break;
    case 'panLeft': scale = 1.2; x = interpolate(p, [0, 1], [50, -50]); break;
    case 'panRight': scale = 1.2; x = interpolate(p, [0, 1], [-50, 50]); break;
    case 'panUp': scale = 1.2; y = interpolate(p, [0, 1], [60, -60]); break;
  }
  // entrance: fade + punch-in + blur clear
  const inP = interpolate(frame, [0, f(XF)], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const punch = idx === 0 ? 0 : (1 - inP) * 0.08;
  const blur = idx === 0 ? 0 : (1 - inP) * 14;
  const rot = idx === 0 ? 0 : (1 - inP) * (idx % 2 ? 1.5 : -1.5);
  return (
    <AbsoluteFill style={{opacity: idx === 0 ? 1 : inP, overflow: 'hidden'}}>
      <Img src={staticFile(`img/${scene.img}.jpg`)} style={{
        width: '100%', height: '100%', objectFit: 'cover',
        transform: `translate(${x}px, ${y}px) scale(${scale + punch}) rotate(${rot}deg)`,
        filter: `blur(${blur}px) contrast(1.08) saturate(1.05)`,
      }} />
    </AbsoluteFill>
  );
};

const Flash: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 2, 8], [0, 0.55, 0], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#eaffde', opacity: o, mixBlendMode: 'screen'}} />;
};

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const i = Math.floor(frame / 2) % 8;
  return <Img src={staticFile(`grain${i}.png`)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%',
    opacity: 0.12, mixBlendMode: 'overlay', imageRendering: 'pixelated'}} />;
};

const Glow: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const dark = t < VICTORY;
  const pulse = 0.5 + 0.5 * Math.sin(t * 2.2);
  const strength = dark ? interpolate(t, [0, HOOK, VICTORY - 1, VICTORY], [0.35, 0.22, 0.3, 0]) : 0;
  const warm = interpolate(t, [VICTORY - 0.5, VICTORY + 2], [0, 0.22], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 60%, rgba(120,255,90,${strength * (0.5 + 0.5 * pulse)}) 0%, transparent 60%)`, mixBlendMode: 'screen'}} />
      <AbsoluteFill style={{background: `linear-gradient(180deg, rgba(255,190,90,${warm}) 0%, transparent 55%)`, mixBlendMode: 'soft-light'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,0.75) 100%)'}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.55) 0%, transparent 18%, transparent 52%, rgba(0,0,0,0.8) 100%)'}} />
    </>
  );
};

const shakeAt = (frame: number, at: number, amount: number) => {
  const d = frame - f(at);
  if (d < 0 || d > 18) return {x: 0, y: 0};
  const k = amount * Math.exp(-d / 5);
  return {x: (random(`x${frame}`) - 0.5) * k, y: (random(`y${frame}`) - 0.5) * k};
};

const HookText: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const l1 = spring({frame, fps, config: {damping: 12, stiffness: 120}});
  const l2 = spring({frame: frame - 40, fps, config: {damping: 9, stiffness: 160}});
  const out = interpolate(frame, [f(HOOK) - 8, f(HOOK)], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const glitch = frame >= 40 && frame < 52 ? (random(`g${frame}`) - 0.5) * 24 : 0;
  const glowPulse = 20 + 12 * Math.sin(frame / 4);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: 70, opacity: out,
      background: 'radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.35) 45%, transparent 75%)'}}>
      <div style={{fontFamily, fontWeight: 900, color: GREEN, letterSpacing: 10, fontSize: 38, textShadow: '0 2px 10px #000', marginBottom: 30,
        opacity: interpolate(frame, [0, 10], [0, 1]), textTransform: 'uppercase'}}>Haqiqiy voqea</div>
      <div style={{fontFamily, fontWeight: 900, fontSize: 92, lineHeight: 1.05, color: 'white', textAlign: 'center',
        transform: `scale(${0.6 + 0.4 * l1})`, opacity: l1, textShadow: '0 8px 40px rgba(0,0,0,0.9)'}}>
        ULAR QORONG‘IDA <span style={{color: GREEN, textShadow: `0 0 ${glowPulse}px ${GREEN}, 0 0 ${glowPulse * 2}px rgba(140,255,90,0.6)`}}>PORLARDI</span>
      </div>
      <div style={{fontFamily: serif, fontStyle: 'italic', fontWeight: 700, fontSize: 78, color: '#ff4d4d', marginTop: 36, textAlign: 'center',
        opacity: Math.min(1, l2), transform: `translateX(${glitch}px) scale(${1.4 - 0.4 * Math.min(1, l2)})`,
        textShadow: `${glitch / 3}px 0 #00ffd5, ${-glitch / 3}px 0 #ff00aa, 0 6px 30px rgba(0,0,0,0.9)`}}>
        …va bu ularni o‘ldirdi
      </div>
    </AbsoluteFill>
  );
};

type W = {w: string; s: number; e: number; end_sent?: boolean};
const chunks: W[][] = (() => {
  const res: W[][] = []; let cur: W[] = [];
  for (const w of wordsData.words as W[]) {
    cur.push(w);
    const len = cur.reduce((a, b) => a + b.w.length + 1, 0);
    if (w.end_sent || cur.length >= 3 || len > 20 || /,$/.test(w.w)) {res.push(cur); cur = [];}
  }
  if (cur.length) res.push(cur);
  return res;
})();

const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps - HOOK;
  const idx = chunks.findIndex((c, i) => {
    const next = chunks[i + 1];
    const end = next ? Math.min(next[0].s, c[c.length - 1].e + 0.6) : c[c.length - 1].e + 0.8;
    return t >= c[0].s - 0.05 && t < end;
  });
  if (idx < 0) return null;
  const c = chunks[idx];
  const local = frame - f(HOOK + c[0].s - 0.05);
  const pop = spring({frame: local, fps, config: {damping: 11, stiffness: 200, mass: 0.6}});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 470}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '6px 22px', maxWidth: 960,
        transform: `scale(${0.75 + 0.25 * pop}) translateY(${(1 - pop) * 40}px)`, opacity: Math.min(1, pop * 1.5)}}>
        {c.map((w, i) => {
          const active = t >= w.s - 0.03 && t < (c[i + 1]?.s ?? w.e + 0.6);
          const spoken = t >= w.s - 0.03;
          const wp = spring({frame: frame - f(HOOK + w.s), fps, config: {damping: 10, stiffness: 260}});
          return (
            <span key={i} style={{fontFamily, fontWeight: 900, fontSize: 84, textTransform: 'uppercase',
              color: active ? GREEN : spoken ? 'white' : 'rgba(255,255,255,0.85)',
              transform: `scale(${active ? 1 + 0.1 * wp : 1})`, display: 'inline-block',
              WebkitTextStroke: '3px rgba(0,0,0,0.85)', paintOrder: 'stroke fill',
              textShadow: active ? `0 0 28px rgba(140,255,90,0.85), 0 6px 0 rgba(0,0,0,0.6)` : '0 6px 0 rgba(0,0,0,0.6), 0 0 24px rgba(0,0,0,0.8)'}}>
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Tag: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const n = Math.min(text.length, Math.floor(frame / 2));
  const o = interpolate(frame, [0, 6, 70, 80], [0, 1, 1, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{padding: '170px 70px', opacity: o}}>
      <div style={{alignSelf: 'flex-start', fontFamily, fontWeight: 800, fontSize: 44, color: '#111', background: GREEN,
        padding: '12px 26px', borderRadius: 10, letterSpacing: 2, boxShadow: `0 0 40px rgba(140,255,90,0.6)`,
        transform: `translateX(${interpolate(frame, [0, 10], [-60, 0], {extrapolateRight: 'clamp', easing: Easing.out(Easing.back(2))})}px)`}}>
        {text.slice(0, n)}{n < text.length ? '▍' : ''}
      </div>
    </AbsoluteFill>
  );
};

const Header: React.FC = () => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 15], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{alignItems: 'center', paddingTop: 95, opacity: o * 0.92}}>
      <div style={{fontFamily, fontWeight: 800, fontSize: 36, letterSpacing: 8, color: 'white', textShadow: '0 2px 12px #000'}}>
        RADIY <span style={{color: GREEN}}>QIZLARI</span>
      </div>
    </AbsoluteFill>
  );
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(frame / durationInFrames) * 100}%`,
    background: GREEN, boxShadow: `0 0 18px ${GREEN}`}} />;
};

const Subscribe: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 10, stiffness: 140}});
  const click = frame > 45 && frame < 60;
  const subscribed = frame >= 52;
  const bell = frame > 60 ? Math.sin((frame - 60) / 2) * 18 * Math.exp(-(frame - 60) / 25) : 0;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: 300}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, transform: `scale(${s * (click ? 0.92 : 1)})`, opacity: s}}>
        <div style={{fontFamily, fontWeight: 900, fontSize: 52, padding: '22px 48px', borderRadius: 60,
          background: subscribed ? '#333' : '#ff2a2a', color: 'white', boxShadow: '0 12px 40px rgba(0,0,0,0.6)'}}>
          {subscribed ? '✓ OBUNA BO‘LDINGIZ' : 'OBUNA BO‘LING'}
        </div>
        <svg width="86" height="86" viewBox="0 0 24 24" style={{transform: `rotate(${bell}deg)`, filter: 'drop-shadow(0 6px 12px rgba(0,0,0,0.6))'}}>
          <path fill="white" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11a7 7 0 0 0-5.5-6.84V3a1.5 1.5 0 0 0-3 0v1.16A7 7 0 0 0 5 11v5l-2 2v1h18v-1z" />
        </svg>
      </div>
      <div style={{position: 'absolute', top: 360, left: 640, width: 70, height: 70, borderRadius: 35, background: 'rgba(255,255,255,0.9)', border: '6px solid rgba(0,0,0,0.4)', opacity: frame > 25 && frame < 75 ? 1 : 0,
        transform: `translate(${interpolate(frame, [25, 45], [180, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}px, ${interpolate(frame, [25, 45], [200, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}px) scale(${click ? 0.7 : 1})`}} />
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  const frame = useCurrentFrame();
  const scenes = scenesData.scenes as Scene[];
  const a = shakeAt(frame, HOOK - 0.08, 34), b = shakeAt(frame, VICTORY, 22), c = shakeAt(frame, 1.5, 16);
  const sx = a.x + b.x + c.x, sy = a.y + b.y + c.y;
  const tagged = scenes.filter((s) => s.tag);
  return (
    <AbsoluteFill style={{background: 'black'}}>
      <AbsoluteFill style={{transform: `translate(${sx}px, ${sy}px) scale(1.03)`}}>
        {scenes.map((s, i) => (
          <Sequence key={i} from={f(s.start)} durationInFrames={f(s.end - s.start + XF) + 1}>
            <KenBurns scene={s} idx={i} />
          </Sequence>
        ))}
      </AbsoluteFill>
      {scenes.slice(1).map((s, i) => [1, 2, 13, 19].includes(i + 1) ? (
        <Sequence key={`fl${i}`} from={f(s.start)} durationInFrames={10}><Flash /></Sequence>) : null)}
      <Sequence from={f(HOOK - 0.1)} durationInFrames={10}><Flash /></Sequence>
      <Glow />
      <Grain />
      <Sequence from={0} durationInFrames={f(HOOK)}><HookText /></Sequence>
      <Sequence from={f(HOOK)}><Header /></Sequence>
      {tagged.map((s, i) => (
        <Sequence key={`t${i}`} from={f(s.start) + 4} durationInFrames={80}><Tag text={s.tag!} /></Sequence>
      ))}
      <Captions />
      <Sequence from={f(HOOK + 53.9)}><Subscribe /></Sequence>
      <Progress />
      <Audio src={staticFile('music.wav')} volume={0.55} />
      <Sequence from={f(HOOK)}><Audio src={staticFile('voice.wav')} volume={1} /></Sequence>
    </AbsoluteFill>
  );
};
