import React from 'react';
import {AbsoluteFill, Img, interpolate, Easing, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig, random} from 'remotion';
import '@fontsource/oswald/700.css';
import '@fontsource/montserrat/600.css';
import '@fontsource/montserrat/800.css';

const titleFont = 'Oswald';
const bodyFont = 'Montserrat';

type Scene = {start: number; end: number; img: string; hook: string | null};
type Word = {s: number; e: number; w: string};
type Line = {s: number; e: number; words: Word[]};
export type StoryProps = {scenes: Scene[]; lines: Line[]};

const FPS = 30;
const XF = 0.8; // crossfade seconds

// Ken Burns move variants
const moves = [
  {z0: 1.05, z1: 1.22, x0: 0, x1: -3, y0: 0, y1: -2},
  {z0: 1.25, z1: 1.06, x0: 2, x1: -2, y0: 1, y1: 0},
  {z0: 1.1, z1: 1.2, x0: -4, x1: 4, y0: 0, y1: 0},
  {z0: 1.2, z1: 1.1, x0: 0, x1: 0, y0: -3, y1: 3},
  {z0: 1.08, z1: 1.25, x0: 3, x1: 0, y0: 2, y1: -1},
];

const SceneImage: React.FC<{scene: Scene; i: number; durF: number}> = ({scene, i, durF}) => {
  const f = useCurrentFrame();
  const m = moves[i % moves.length];
  const p = interpolate(f, [0, durF], [0, 1], {extrapolateRight: 'clamp', easing: Easing.inOut(Easing.sin)});
  const z = m.z0 + (m.z1 - m.z0) * p;
  const x = m.x0 + (m.x1 - m.x0) * p;
  const y = m.y0 + (m.y1 - m.y0) * p;
  const xfF = XF * FPS;
  const opacity = interpolate(f, [0, xfF], [0, 1], {extrapolateRight: 'clamp'});
  const blur = interpolate(f, [0, xfF], [12, 0], {extrapolateRight: 'clamp'});
  const bright = interpolate(f, [0, 6, xfF], [1.6, 1.25, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity}}>
      <Img
        src={staticFile(scene.img)}
        style={{
          width: '100%', height: '100%', objectFit: 'cover',
          transform: `scale(${z}) translate(${x}%, ${y}%)`,
          filter: `blur(${blur}px) brightness(${bright}) contrast(1.08) saturate(0.85) sepia(0.12)`,
        }}
      />
    </AbsoluteFill>
  );
};

const HookText: React.FC<{text: string; big: boolean}> = ({text, big}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame: f, fps, config: {damping: 14, stiffness: 120}});
  const out = interpolate(f, [fps * 3.2, fps * 3.9], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const track = interpolate(f, [0, fps * 3.9], [0.35, 0.12]);
  const jitter = f < 10 ? (random(`j${f}`) - 0.5) * 18 : 0;
  return (
    <AbsoluteFill style={{justifyContent: big ? 'center' : 'flex-start', alignItems: big ? 'center' : 'flex-start', padding: big ? 0 : '110px 120px', opacity: out}}>
      <div style={{
        fontFamily: titleFont, fontWeight: 700, color: '#f4ead5',
        fontSize: big ? 260 : 86, letterSpacing: `${track}em`, textTransform: 'uppercase',
        transform: `scale(${0.6 + 0.4 * sp}) translateX(${jitter}px)`, opacity: sp,
        textShadow: '0 0 40px rgba(0,0,0,0.9), 0 6px 18px rgba(0,0,0,0.8)',
        borderLeft: big ? 'none' : '10px solid #c8352b', paddingLeft: big ? 0 : 30,
      }}>{text}</div>
    </AbsoluteFill>
  );
};

const IntroTitle: React.FC = () => {
  // Hook card that sits over the first scene, after the "29 YIL" slam
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame: f, fps, config: {damping: 200}});
  const out = interpolate(f, [fps * 4.2, fps * 5], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const lineW = interpolate(f, [0, fps * 1.2], [0, 620], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: out}}>
      <div style={{fontFamily: bodyFont, fontWeight: 600, color: '#d9cfb8', fontSize: 34, letterSpacing: '0.5em', opacity: a}}>HAQIQIY TARIX</div>
      <div style={{height: 4, width: lineW, background: '#c8352b', margin: '26px 0'}} />
      <div style={{fontFamily: titleFont, fontWeight: 700, color: '#fff', fontSize: 104, textAlign: 'center', lineHeight: 1.05, transform: `translateY(${(1 - a) * 40}px)`, opacity: a, textShadow: '0 8px 30px rgba(0,0,0,.9)'}}>
        URUSH TUGAGANINI<br />BILMAGAN ASKAR
      </div>
    </AbsoluteFill>
  );
};

const Subtitles: React.FC<{lines: Line[]}> = ({lines}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const line = lines.find((l) => t >= l.s - 0.05 && t <= l.e + 0.25);
  if (!line) return null;
  const inP = interpolate(t, [line.s - 0.05, line.s + 0.15], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 120}}>
      <div style={{maxWidth: 1500, textAlign: 'center', fontFamily: bodyFont, fontWeight: 800, fontSize: 54, lineHeight: 1.25,
        opacity: inP, transform: `translateY(${(1 - inP) * 14}px)`}}>
        {line.words.map((w, k) => {
          const active = t >= w.s && t < w.e + 0.05;
          const done = t >= w.e;
          return (
            <span key={k} style={{
              color: active ? '#ffd166' : done ? '#ffffff' : 'rgba(255,255,255,0.72)',
              textShadow: '0 3px 0 #000, 0 0 18px rgba(0,0,0,0.95), 0 0 4px #000',
              display: 'inline-block', margin: '0 9px',
              transform: active ? 'scale(1.08)' : 'scale(1)',
            }}>{w.w}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  const seed = f % 8;
  const flicker = 0.97 + random(`fl${f}`) * 0.05;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.75) 100%)'}} />
      <AbsoluteFill style={{background: `rgba(0,0,0,${1 - flicker})`}} />
      <svg width="1920" height="1080" style={{position: 'absolute', opacity: 0.11, mixBlendMode: 'overlay'}}>
        <filter id={`n${seed}`}><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} /></filter>
        <rect width="100%" height="100%" filter={`url(#n${seed})`} />
      </svg>
      {/* cinematic letterbox */}
      <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 60, background: '#000'}} />
      <div style={{position: 'absolute', bottom: 0, left: 0, right: 0, height: 60, background: '#000'}} />
    </AbsoluteFill>
  );
};

const Subscribe: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame: f, fps, config: {damping: 12}});
  const clicked = f > fps * 2.2;
  const press = spring({frame: f - fps * 2.0, fps, config: {damping: 10, stiffness: 200}});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', top: -120}}>
      <div style={{display: 'flex', gap: 30, transform: `scale(${a})`}}>
        <div style={{fontFamily: bodyFont, fontWeight: 800, fontSize: 52, padding: '22px 54px', borderRadius: 18,
          background: clicked ? '#3a3a3a' : '#e62117', color: '#fff', transform: `scale(${1 - 0.08 * Math.sin(Math.min(press, 1) * Math.PI)})`,
          boxShadow: '0 12px 40px rgba(0,0,0,.6)'}}>{clicked ? 'OBUNA BO‘LINDI ✓' : 'OBUNA BO‘LING'}</div>
        <div style={{fontFamily: bodyFont, fontWeight: 800, fontSize: 52, padding: '22px 40px', borderRadius: 18, background: 'rgba(255,255,255,.92)', color: '#111'}}>🔔</div>
      </div>
    </AbsoluteFill>
  );
};

export const Story: React.FC<StoryProps> = ({scenes, lines}) => {
  const f = useCurrentFrame();
  const total = scenes[scenes.length - 1].end;
  const fadeOut = interpolate(f / FPS, [total - 2, total], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeIn = interpolate(f, [0, 12], [1, 0], {extrapolateRight: 'clamp'});
  // white flash on the "29 YIL" hook slam
  const flash = interpolate(f, [0, 3, 14], [0, 0.9, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {scenes.map((sc, i) => {
        const from = Math.round(sc.start * FPS);
        const to = Math.round((i + 1 < scenes.length ? scenes[i + 1].start + XF : sc.end) * FPS);
        return (
          <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)}>
            <SceneImage scene={sc} i={i} durF={to - from} />
          </Sequence>
        );
      })}
      <Grain />
      {scenes.map((sc, i) => sc.hook ? (
        <Sequence key={`h${i}`} from={Math.round(sc.start * FPS) + (i === 0 ? 0 : 12)} durationInFrames={4 * FPS}>
          <HookText text={sc.hook} big={i === 0 || sc.hook === 'SIZ-CHI?'} />
        </Sequence>
      ) : null)}
      <Sequence from={Math.round(4.2 * FPS)} durationInFrames={5 * FPS}>
        <IntroTitle />
      </Sequence>
      <Subtitles lines={lines} />
      <Sequence from={Math.round(scenes[scenes.length - 1].start * FPS) + 15} durationInFrames={Math.round((scenes[scenes.length - 1].end - scenes[scenes.length - 1].start) * FPS)}>
        <Subscribe />
      </Sequence>
      <AbsoluteFill style={{background: '#fff', opacity: flash}} />
      <AbsoluteFill style={{background: '#000', opacity: Math.max(fadeIn, fadeOut)}} />
    </AbsoluteFill>
  );
};
