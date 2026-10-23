import React from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

export type Scene = {id: string; start: number; end: number; era: string};
export type Sub = {start: number; end: number; words: {w: string; s: number}[]};
export type Card = {label: string; year: string; start: number};
export type Timeline = {fps: number; hook: number; total: number; scenes: Scene[]; subs: Sub[]; cards: Card[]};

const GOLD = '#FFC94A';
const FADE = 0.7;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const fontCss = `
@font-face{font-family:Mont;font-weight:500;src:url(${staticFile('fonts/montserrat-latin-500-normal.woff2')})}
@font-face{font-family:Mont;font-weight:700;src:url(${staticFile('fonts/montserrat-latin-700-normal.woff2')})}
@font-face{font-family:Mont;font-weight:800;src:url(${staticFile('fonts/montserrat-latin-800-normal.woff2')})}
@font-face{font-family:Mont;font-weight:900;src:url(${staticFile('fonts/montserrat-latin-900-normal.woff2')})}
@font-face{font-family:Mont;font-weight:700;src:url(${staticFile('fonts/montserrat-latin-ext-700-normal.woff2')});unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Mont;font-weight:800;src:url(${staticFile('fonts/montserrat-latin-ext-800-normal.woff2')});unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Mont;font-weight:900;src:url(${staticFile('fonts/montserrat-latin-ext-900-normal.woff2')});unicode-range:U+0100-024F,U+1E00-1EFF}
@font-face{font-family:Play;font-weight:700;src:url(${staticFile('fonts/playfair-display-latin-700-normal.woff2')})}
@font-face{font-family:Play;font-weight:900;src:url(${staticFile('fonts/playfair-display-latin-900-normal.woff2')})}
`;

// Uzbek typography: o' g' -> o‘ g‘, other apostrophes -> ’
const uz = (s: string) => s.replace(/([oOgG])'/g, '$1‘').replace(/'/g, '’');

const ERA_FILTER: Record<string, string> = {
  now: 'saturate(1.08) contrast(1.04)',
  '1404': 'sepia(0.18) saturate(1.2) contrast(1.06) brightness(1.02)',
  '1980': 'sepia(0.55) saturate(0.85) contrast(1.06) hue-rotate(-8deg)',
  '1950': 'grayscale(1) contrast(1.18) brightness(0.95)',
};

const KenBurns: React.FC<{src: string; i: number; progress: number; filter: string; extraScale?: number}> = ({src, i, progress, filter, extraScale = 0}) => {
  const zoomIn = i % 3 !== 1;
  const p = Easing.inOut(Easing.sin)(Math.min(1, Math.max(0, progress)));
  const scale = (zoomIn ? interpolate(p, [0, 1], [1.06, 1.24]) : interpolate(p, [0, 1], [1.24, 1.06])) + extraScale;
  const dir = random(`dx${i}`) > 0.5 ? 1 : -1;
  const dy = random(`dy${i}`) > 0.5 ? 1 : -1;
  const x = interpolate(p, [0, 1], [-2.2 * dir, 2.2 * dir]);
  const y = interpolate(p, [0, 1], [-1.2 * dy, 1.2 * dy]);
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img src={staticFile(`img/${src}.jpg`)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale}) translate(${x}%, ${y}%)`, filter}} />
    </AbsoluteFill>
  );
};

const Scenes: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const t = frame / tl.fps;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {tl.scenes.map((s, i) => {
        if (t < s.start || t > s.end + FADE) return null;
        const prevEra = i > 0 ? tl.scenes[i - 1].era : s.era;
        const eraChange = prevEra !== s.era;
        const fadeIn = i === 0 ? 1 : interpolate(t, [s.start, s.start + (eraChange ? 0.35 : FADE)], [0, 1], clamp);
        const progress = (t - s.start) / (s.end + FADE - s.start);
        // punch-in on era change
        const punch = eraChange ? interpolate(t, [s.start, s.start + 0.6], [0.12, 0], {...clamp, easing: Easing.out(Easing.cubic)}) : 0;
        const blur = eraChange ? interpolate(t, [s.start, s.start + 0.5], [14, 0], clamp) : interpolate(fadeIn, [0, 1], [4, 0]);
        return (
          <AbsoluteFill key={s.id} style={{opacity: fadeIn}}>
            <KenBurns src={s.id} i={i} progress={progress} filter={`${ERA_FILTER[s.era]} blur(${blur}px)`} extraScale={punch} />
          </AbsoluteFill>
        );
      })}
      {tl.scenes.map((s, i) => {
        if (i === 0 || tl.scenes[i - 1].era === s.era) return null;
        const o = interpolate(t, [s.start - 0.08, s.start, s.start + 0.45], [0, 0.85, 0], clamp);
        return o > 0 ? <AbsoluteFill key={'f' + s.id} style={{background: '#fff8e6', opacity: o, mixBlendMode: 'screen'}} /> : null;
      })}
    </AbsoluteFill>
  );
};

const Particles: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const t = frame / tl.fps;
  const era = tl.scenes.find((s) => t >= s.start && t < s.end)?.era ?? 'now';
  const color = era === '1950' ? '255,255,255' : era === 'now' ? '170,210,255' : '255,214,140';
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {new Array(46).fill(0).map((_, k) => {
        const speed = 0.4 + random(`s${k}`) * 1.2;
        const x = random(`x${k}`) * 1920 + Math.sin(frame / (40 + k) + k) * 30;
        const y = 1080 - ((random(`y${k}`) * 1200 + frame * speed) % 1200);
        const size = 1.5 + random(`r${k}`) * 4;
        const tw = 0.25 + 0.5 * Math.abs(Math.sin(frame / 25 + k));
        return <div key={k} style={{position: 'absolute', left: x, top: y, width: size, height: size, borderRadius: '50%', background: `rgba(${color},${tw})`, boxShadow: `0 0 ${size * 3}px rgba(${color},${tw})`}} />;
      })}
    </AbsoluteFill>
  );
};

const FilmLook: React.FC = () => {
  const frame = useCurrentFrame();
  const leak = 0.18 + 0.12 * Math.sin(frame / 70);
  const lx = 50 + 40 * Math.sin(frame / 160);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill style={{background: `radial-gradient(circle at ${lx}% 0%, rgba(255,150,60,${leak}) 0%, rgba(255,120,40,0) 45%)`, mixBlendMode: 'screen'}} />
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('grain.png')})`, backgroundPosition: `${Math.floor(random(`g${frame}`) * 512)}px ${Math.floor(random(`h${frame}`) * 512)}px`, opacity: 0.07, mixBlendMode: 'overlay'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 50%, rgba(0,0,0,0.62) 100%)'}} />
      <AbsoluteFill style={{background: 'linear-gradient(to top, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0) 32%)'}} />
    </AbsoluteFill>
  );
};

const Subtitles: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const sub = tl.subs.find((s) => t >= s.start && t < s.end);
  if (!sub) return null;
  const local = frame - Math.round(sub.start * fps);
  const pop = spring({frame: local, fps, config: {damping: 14, stiffness: 180}});
  const out = interpolate(t, [sub.end - 0.15, sub.end], [1, 0], clamp);
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 92}}>
      <div style={{maxWidth: 1500, textAlign: 'center', fontFamily: 'Mont', fontWeight: 800, fontSize: 54, lineHeight: 1.25, color: '#fff', opacity: out, transform: `translateY(${(1 - pop) * 24}px) scale(${0.94 + 0.06 * pop})`, textShadow: '0 4px 18px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)'}}>
        {sub.words.map((w, k) => {
          const active = t >= w.s && (k === sub.words.length - 1 || t < sub.words[k + 1].s);
          const said = t >= w.s;
          return (
            <span key={k} style={{display: 'inline-block', margin: '0 11px', color: active ? GOLD : said ? '#fff' : 'rgba(255,255,255,0.72)', textShadow: active ? '0 0 22px rgba(255,201,74,0.55), 0 4px 18px rgba(0,0,0,0.85)' : undefined}}>
              {uz(w.w)}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const EraCard: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const c = tl.cards.find((c) => t >= c.start && t < c.start + 3.6);
  if (!c) return null;
  const local = frame - Math.round(c.start * fps);
  const s = spring({frame: local, fps, config: {damping: 18, stiffness: 120}});
  const out = interpolate(t, [c.start + 3.0, c.start + 3.6], [1, 0], clamp);
  const line = interpolate(local, [6, 30], [0, 260], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{padding: '90px 110px', opacity: out}}>
      <div style={{fontFamily: 'Play', fontWeight: 900, fontSize: 190, color: GOLD, lineHeight: 1, letterSpacing: interpolate(s, [0, 1], [60, 6]), opacity: s, textShadow: '0 8px 40px rgba(0,0,0,0.7)'}}>{c.year}</div>
      <div style={{height: 4, width: line, background: GOLD, margin: '18px 0', boxShadow: '0 0 18px rgba(255,201,74,0.8)'}} />
      <div style={{fontFamily: 'Mont', fontWeight: 700, fontSize: 40, letterSpacing: 14, color: '#fff', opacity: interpolate(local, [12, 30], [0, 1], clamp), transform: `translateX(${interpolate(local, [12, 30], [-30, 0], clamp)}px)`, textShadow: '0 4px 18px rgba(0,0,0,0.8)'}}>{c.label}</div>
    </AbsoluteFill>
  );
};

const HOOK_SHOTS = [
  {img: 's03', year: '2026', era: 'now'},
  {img: 's48', year: '1950', era: '1950'},
  {img: 's38', year: '1980', era: '1980'},
  {img: 's10', year: '1404', era: '1404'},
];

const Hook: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const end = Math.round(tl.hook * fps);
  if (frame >= end + 12) return null;
  const SHOT = 20;
  const shotsEnd = HOOK_SHOTS.length * SHOT + 6;
  const fadeToStory = interpolate(frame, [end - 6, end + 12], [1, 0], clamp);
  let content: React.ReactNode;
  if (frame < shotsEnd) {
    const k = Math.min(HOOK_SHOTS.length - 1, Math.floor(frame / SHOT));
    const sh = HOOK_SHOTS[k];
    const lf = frame - k * SHOT;
    const shake = (random(`sh${frame}`) - 0.5) * interpolate(lf, [0, 6], [26, 0], clamp);
    const yScale = interpolate(lf, [0, 5], [1.6, 1], {...clamp, easing: Easing.out(Easing.back(2))});
    content = (
      <AbsoluteFill>
        <AbsoluteFill style={{transform: `scale(${1.25 + lf * 0.012}) translateX(${shake}px)`}}>
          <Img src={staticFile(`img/${sh.img}.jpg`)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: `${ERA_FILTER[sh.era]} brightness(0.7)`}} />
        </AbsoluteFill>
        <AbsoluteFill style={{background: '#fff', opacity: interpolate(lf, [0, 4], [0.7, 0], clamp)}} />
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
          <div style={{fontFamily: 'Play', fontWeight: 900, fontSize: 300, color: k === 3 ? GOLD : '#fff', transform: `scale(${yScale}) translateX(${shake * 0.5}px)`, textShadow: '0 10px 60px rgba(0,0,0,0.8)', letterSpacing: 10}}>{sh.year}</div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  } else {
    const lf = frame - shotsEnd;
    const a = spring({frame: lf, fps, config: {damping: 16, stiffness: 140}});
    const b = spring({frame: lf - 8, fps, config: {damping: 12, stiffness: 160}});
    const c = spring({frame: lf - 18, fps, config: {damping: 16, stiffness: 140}});
    const d = interpolate(lf, [40, 56], [0, 1], clamp);
    content = (
      <AbsoluteFill>
        <AbsoluteFill style={{transform: `scale(${1.1 + lf * 0.0015})`}}>
          <Img src={staticFile('img/s12.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', filter: `${ERA_FILTER['1404']} brightness(0.45) blur(3px)`}} />
        </AbsoluteFill>
        <AbsoluteFill style={{background: '#fff', opacity: interpolate(lf, [0, 6], [0.8, 0], clamp)}} />
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
          <div style={{fontFamily: 'Mont', fontWeight: 700, fontSize: 52, letterSpacing: 18, color: '#fff', opacity: a, transform: `translateY(${(1 - a) * -30}px)`}}>AGAR SIZ</div>
          <div style={{fontFamily: 'Play', fontWeight: 900, fontSize: 190, color: GOLD, lineHeight: 1.05, transform: `scale(${0.6 + 0.4 * b})`, opacity: Math.min(1, b * 1.4), textShadow: '0 10px 50px rgba(0,0,0,0.85)'}}>1404-yilda</div>
          <div style={{fontFamily: 'Mont', fontWeight: 900, fontSize: 84, color: '#fff', opacity: c, transform: `translateY(${(1 - c) * 40}px)`, textShadow: '0 6px 30px rgba(0,0,0,0.8)'}}>{uz("YASHAGANINGIZDA EDI...?")}</div>
          <div style={{marginTop: 36, fontFamily: 'Mont', fontWeight: 500, fontSize: 36, color: 'rgba(255,255,255,0.88)', opacity: d}}>{uz("Na MacBook, na internet, na sun'iy intellekt...")}</div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  return <AbsoluteFill style={{opacity: fadeToStory}}>{content}</AbsoluteFill>;
};

const Outro: React.FC<{tl: Timeline}> = ({tl}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const st = Math.round((tl.total - 4.2) * fps);
  if (frame < st) return null;
  const lf = frame - st;
  const a = spring({frame: lf, fps, config: {damping: 18}});
  const black = interpolate(frame, [tl.total * fps - 30, tl.total * fps - 2], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: 'rgba(0,0,0,0.45)', opacity: a}} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center', opacity: a}}>
        <div style={{fontFamily: 'Mont', fontWeight: 700, fontSize: 40, letterSpacing: 16, color: '#fff'}}>{uz('HAR BIR SONIYANING')}</div>
        <div style={{fontFamily: 'Play', fontWeight: 900, fontSize: 150, color: GOLD, transform: `scale(${0.85 + 0.15 * a})`, textShadow: '0 10px 50px rgba(0,0,0,0.8)'}}>qadriga yeting</div>
        <div style={{marginTop: 20, fontFamily: 'Mont', fontWeight: 800, fontSize: 34, letterSpacing: 8, color: 'rgba(255,255,255,0.85)'}}>{uz('"AGAR SEN...?" LOYIHASI')}</div>
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#000', opacity: black}} />
    </AbsoluteFill>
  );
};

export const Main: React.FC<{timeline: Timeline}> = ({timeline: tl}) => {
  const frame = useCurrentFrame();
  const inStory = frame >= tl.hook * tl.fps - 6;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <style>{fontCss}</style>
      {inStory && <Scenes tl={tl} />}
      {inStory && <Particles tl={tl} />}
      <FilmLook />
      <Hook tl={tl} />
      {inStory && <EraCard tl={tl} />}
      {inStory && frame < (tl.total - 4.2) * tl.fps && <Subtitles tl={tl} />}
      <Outro tl={tl} />
    </AbsoluteFill>
  );
};
