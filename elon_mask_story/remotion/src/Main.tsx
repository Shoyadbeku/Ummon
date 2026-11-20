import React from 'react';
import {AbsoluteFill, Audio, interpolate, random, Sequence, spring, staticFile, useCurrentFrame} from 'remotion';
import {
  CYAN, f, FPS, GOLD, Grain, GREEN, Headline, LightLeak, OVER, Pill, RED, Shot, Stamp, SZ, Vignette, YearRoll, YELLOW, Zzz,
} from './fx';
import * as C from './comps';
import {DURATION, LEAKS, OVERLAYS, SFX, SHAKES, SHOTS} from './timeline';

const GOLD_GRAD = 'linear-gradient(180deg,#FFF6C8 0%,#FFD23F 45%,#E89B0C 100%)';
const ICE_GRAD = 'linear-gradient(180deg,#FFFFFF 0%,#BFF4FF 50%,#4FE3FF 100%)';
const GREEN_GRAD = 'linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)';
const RED_GRAD = 'linear-gradient(180deg,#FFD9D9 0%,#FF5A5A 50%,#C40F0F 100%)';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ENTERS = ['whip-up', 'zoom', 'whip-left', 'mask', 'whip-right', 'fade'];
// 16:9: images that must not be cropped (portraits / low resolution) are shown whole over a blurred copy
const CONTAIN = new Set(['musk_2015', 'musk_dark', 'musk_royal', 'musk_smile', 'musk_young', 'hoover', 'mosaic', 'omelek', 'falcon1', 'compaq', 'merlin']);
// overlay positions were authored on a 1920-tall canvas -> map to 1080
const Y = (y: number) => Math.max(70, Math.min(860, Math.round(y * 0.5625)));
const PILL_BG: Record<string, string> = {cyan: CYAN, green: GREEN, red: RED, white: '#ffffff', yellow: YELLOW};

/** Full-screen motion-graphics scene with a zoom/blur entrance. */
const CompShot: React.FC<{from: number; to: number; children: React.ReactNode}> = ({from, to, children}) => (
  <Sequence from={f(from)} durationInFrames={f(to) - f(from) + OVER} layout="none">
    <CompEnter>{children}</CompEnter>
  </Sequence>
);
const CompEnter: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 8], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: p, transform: `scale(${1.15 - 0.15 * p})`, filter: p < 1 ? `blur(${(1 - p) * 24}px)` : undefined, backgroundColor: '#05060a'}}>{children}</AbsoluteFill>;
};

const comp = (name: string, base: number): React.ReactNode => {
  switch (name) {
    case 'brothers': return <C.Brothers variant={1} />;
    case 'brothers2': return <C.Brothers variant={2} />;
    case 'noapps': return <C.NoApps base={base} />;
    case 'namemorph': return <C.NameMorph base={base} />;
    case 'citymap': return <C.CityMap />;
    case 'needs': return <C.Needs base={base} />;
    case 'daynight': return <C.DayNight base={base} />;
    case 'chart': return <C.InternetChart />;
    case 'browser': return <C.BrowserScene base={base} />;
    case 'printweb': return <C.PrintWeb />;
    case 'org1': return <C.OrgChart label="TAJRIBALI RAHBAR" base={base} strikeAt={232.8} />;
    case 'org2': return <C.OrgChart year="2000" label="CHETLATILADI" base={base} strikeAt={316.4} />;
    case 'control': return <C.Control />;
    case 'xcom': return <C.WordMark text="X.com" sub="YANGI INTERNET KOMPANIYA" color={CYAN} />;
    case 'transfer': return <C.Transfer />;
    case 'merge': return <C.Merge />;
    case 'stake': return <C.Stake />;
    case 'ebay': return <C.Ebay />;
    case 'safe_risky': return <C.SafeRisky base={base} />;
    case 'rocket_vs_code': return <C.RocketVsCode />;
    case 'attempts_fail': return <C.Attempts base={base} />;
    case 'attempts_win': return <C.Attempts win base={base} />;
    case 'founders': return <C.Founders base={base} />;
    case 'split_sx_tesla': return <C.SplitSxTesla />;
    case 'timeline': return <C.CareerTimeline base={base} />;
    case 'recap': return <C.Recap base={base} />;
    case 'question': return <C.Question />;
    case 'final_split': return <C.FinalSplit base={base} />;
    case 'comment': return <C.Comment />;
    default: return null;
  }
};

const Shots: React.FC = () => (
  <>
    {SHOTS.map(([t, src, o = {}], i) => {
      const to = i + 1 < SHOTS.length ? SHOTS[i + 1][0] : DURATION;
      if (typeof src === 'string' && src.startsWith('comp:')) return <CompShot key={i} from={t} to={to}>{comp(src.slice(5), t)}</CompShot>;
      const img = typeof src === 'string' && src.startsWith('img:');
      const path = typeof src === 'number' ? `v/mk_${src}.mp4` : img ? `img/${src.slice(4)}.jpg` : `v/${src}.mp4`;
      const kb = o.kb ?? (i % 2 ? [1.18, 1.08] : [1.08, 1.2]);
      const contain = img && CONTAIN.has((src as string).slice(4));
      return (
        <Shot key={i} src={path} img={img} contain={contain} from={t} to={to} enter={(o.e ?? ENTERS[i % ENTERS.length]) as any} kb={kb as [number, number]} drift={o.drift ?? [0, 0]}
          pos={contain ? 'center' : o.pos ?? 'center'} grade={o.bw ? 'bw' : o.g ?? 'cine'} startFrom={o.sf ?? 0} rate={o.rate ?? 1} />
      );
    })}
  </>
);

const styleProps = (style?: string) => {
  switch (style) {
    case 'gold': return {gradient: GOLD_GRAD, glow: 'rgba(255,200,60,0.6)'};
    case 'ice': return {gradient: ICE_GRAD, glow: 'rgba(79,227,255,0.7)'};
    case 'green': return {gradient: GREEN_GRAD, glow: 'rgba(61,255,138,0.6)'};
    case 'red': return {gradient: RED_GRAD, glow: 'rgba(255,60,60,0.6)'};
    default: return {color: 'white'};
  }
};

const Strike: React.FC<{y: number; size: number}> = ({y, size}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [12, 22], [0, 1], clamp);
  return <div style={{position: 'absolute', left: 560, top: y + size * 0.48, height: 14, width: 800 * p, background: RED, borderRadius: 8, boxShadow: `0 0 20px ${RED}`}} />;
};

const Overlays: React.FC = () => (
  <>
    {OVERLAYS.map((o, i) => {
      const from = f(o.t);
      const dur = Math.max(1, f(o.u) - f(o.t));
      switch (o.k) {
        case 'title':
          return (
            <React.Fragment key={i}>
              <Headline text={o.text} at={o.t} until={o.u} y={Y(o.y)} size={Math.round((o.size ?? 150) * SZ)} stagger={o.stagger ?? 1.1} {...styleProps(o.style)} />
              {o.strike && <Sequence from={from} durationInFrames={dur} layout="none"><Strike y={Y(o.y)} size={Math.round((o.size ?? 150) * SZ)} /></Sequence>}
            </React.Fragment>
          );
        case 'pill':
          return <Pill key={i} text={o.text} at={o.t} until={o.u} y={Y(o.y)} bg={PILL_BG[o.bg ?? 'yellow'] ?? o.bg} color={o.color ?? '#111'} size={Math.round((o.size ?? 54) * 0.85)} from={i % 2 ? 'right' : 'left'} />;
        case 'stamp':
          return <Stamp key={i} text={o.text} at={o.t} until={o.u} y={Y(o.y)} size={Math.round((o.size ?? 120) * SZ)} color={o.color === 'red' || !o.color ? RED : o.color} />;
        case 'year':
          return <YearRoll key={i} at={o.t} until={o.u} y={Y(o.y) - 120} from={o.from} to={o.to} suffix={o.suffix ?? '-YIL'} />;
        case 'zzz':
          return <Zzz key={i} at={o.t} until={o.u} x={760} y={520} />;
        default: {
          let el: React.ReactNode = null;
          if (o.k === 'count') el = <C.BigCount to={o.to} prefix={o.prefix} suffix={o.suffix} y={Y(o.y)} label={o.label} dur={o.dur} textOnly={o.textOnly} />;
          if (o.k === 'age') el = <C.AgeBadge n={o.n} y={Y(o.y)} />;
          if (o.k === 'list3') el = <C.List3 items={o.items} y={Y(o.y)} base={o.t} />;
          if (o.k === 'quote') el = <C.Quote text={o.text} by={o.by} y={Y(o.y)} />;
          if (o.k === 'growth') el = <C.Growth y={Y(o.y)} />;
          if (o.k === 'drain') el = <C.Drain y={Y(o.y)} />;
          return <Sequence key={i} from={from} durationInFrames={dur} layout="none"><FadeOut dur={dur}>{el}</FadeOut></Sequence>;
        }
      }
    })}
  </>
);

const FadeOut: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{opacity: interpolate(frame, [dur - 6, dur], [1, 0], clamp)}}>{children}</AbsoluteFill>;
};

/** One camera-shake layer driven by the SHAKES list. */
const ShakeAll: React.FC<{children: React.ReactNode}> = ({children}) => {
  const frame = useCurrentFrame();
  let x = 0, y = 0;
  for (const [t, d, amp] of SHAKES) {
    const local = frame - f(t);
    if (local >= 0 && local < f(d)) {
      const k = 1 - local / f(d);
      x += (random(`x${frame}`) - 0.5) * 2 * amp * k;
      y += (random(`y${frame}`) - 0.5) * 2 * amp * k;
    }
  }
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px)`}}>{children}</AbsoluteFill>;
};

export const Main: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#05060a'}}>
    <ShakeAll>
      <Shots />
    </ShakeAll>
    <Overlays />
    {LEAKS.map(([t, h], i) => <LightLeak key={i} at={t} hue={h} />)}
    <Vignette />
    <Grain opacity={0.08} />
    <Audio src={staticFile('audio/voice_clean.wav')} volume={1} />
    <Audio src={staticFile('audio/music_bed.mp3')} volume={1} />
    {SFX.map(([t, s, v], i) => (
      <Sequence key={i} from={f(t)} durationInFrames={f(3)} layout="none">
        <Audio src={staticFile(`audio/${s}.mp3`)} volume={v} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
