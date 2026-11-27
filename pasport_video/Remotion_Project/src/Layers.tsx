import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Loop,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BODY, C, FPS, HEAD} from './theme';
import meta from './data/meta.json';

type Meta = Record<string, {channel: string; title: string; label: string; url: string}>;
const M = meta as Meta;

export const clipFile = (ref: [string, number], bg = false) =>
  staticFile(`clips/${ref[0]}_${ref[1].toFixed(1)}${bg ? '_bg' : ''}.mp4`);

export const sourceLabel = (id: string) => M[id]?.label ?? '';

/* Real archive footage with a gentle Ken Burns move, documentary grade, vignette. */
export const ClipLayer: React.FC<{
  src: [string, number];
  dur: number; // frames
  seed: number;
  blur?: number;
  loopFrames?: number;
}> = ({src, dur, seed, blur = 0, loopFrames}) => {
  const f = useCurrentFrame();
  const dir = seed % 4;
  const p = interpolate(f, [0, dur], [0, 1], {extrapolateRight: 'clamp'});
  const scale = (dir % 2 === 0 ? 1.04 + 0.06 * p : 1.1 - 0.06 * p) + (blur ? 0.08 : 0);
  const tx = (dir < 2 ? -1 : 1) * 18 * (p - 0.5);
  const ty = (dir === 1 || dir === 2 ? -1 : 1) * 8 * (p - 0.5);
  const video = (
    <OffthreadVideo
      src={clipFile(src, !!blur)}
      muted
      style={{width: '100%', height: '100%', objectFit: 'cover'}}
    />
  );
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: C.navy}}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translate(${tx}px, ${ty}px)`,
        }}
      >
        {loopFrames ? <Loop durationInFrames={loopFrames}>{video}</Loop> : video}
      </AbsoluteFill>
      <Vignette strength={blur ? 0.75 : 0.5} />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{strength?: number}> = ({strength = 0.5}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,${strength}) 100%)`,
      pointerEvents: 'none',
    }}
  />
);

/* Subtle animated film grain (SVG turbulence, seeded per frame). */
export const Grain: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: 0.07, mixBlendMode: 'overlay', pointerEvents: 'none'}}>
      <svg width="1920" height="1080">
        <filter id="g">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 12} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="1920" height="1080" filter="url(#g)" />
      </svg>
    </AbsoluteFill>
  );
};

/* Dark editorial backdrop for motion graphics: optional blurred real footage + grid. */
export const GraphicBg: React.FC<{bg?: [string, number]; dur: number; seed: number}> = ({bg, dur, seed}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: C.navy}}>
      {bg ? (
        <ClipLayer src={bg} dur={dur} seed={seed} blur={14} loopFrames={Math.min(dur, 110)} />
      ) : (
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at ${30 + (f / 20) % 40}% 30%, ${C.navy2} 0%, ${C.navy} 60%)`,
          }}
        />
      )}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.line} 1px, transparent 1px), linear-gradient(90deg, ${C.line} 1px, transparent 1px)`,
          backgroundSize: '96px 96px',
          backgroundPosition: `${-f * 0.3}px ${-f * 0.15}px`,
          opacity: 0.18,
        }}
      />
    </AbsoluteFill>
  );
};

/* On-screen attribution, bottom-right, documentary lower-third style. */
export const SourceLabel: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - 4, fps, config: {damping: 200}});
  if (!text) return null;
  return (
    <div
      style={{
        position: 'absolute',
        right: 40,
        bottom: 30,
        transform: `translateX(${(1 - s) * 40}px)`,
        opacity: s,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '7px 14px 7px 12px',
        background: 'rgba(7,16,31,0.72)',
        borderLeft: `3px solid ${C.gold}`,
        borderRadius: 3,
        fontFamily: BODY,
        fontSize: 19,
        fontWeight: 500,
        letterSpacing: 0.2,
        color: C.ink,
      }}
    >
      <svg width="20" height="14" viewBox="0 0 20 14">
        <rect width="20" height="14" rx="3.5" fill={C.red} />
        <path d="M8 4 L13.5 7 L8 10 Z" fill="#fff" />
      </svg>
      {text}
    </div>
  );
};

/* Big documentary title card used in the hook. */
export const HookTitle: React.FC<{text: string; dur: number}> = ({text, dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(' ');
  const out = interpolate(f, [dur - 10, dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        padding: '0 160px',
        background: 'linear-gradient(90deg, rgba(7,16,31,0.85) 0%, rgba(7,16,31,0.35) 65%, rgba(7,16,31,0) 100%)',
        opacity: out,
      }}
    >
      <div style={{fontFamily: BODY, color: C.gold, fontSize: 26, fontWeight: 700, letterSpacing: 6, marginBottom: 22}}>
        PASPORT KUCHI · HUJJATLI TAHLIL
      </div>
      <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: 82, lineHeight: 1.08, color: C.ink, maxWidth: 1250}}>
        {words.map((w, i) => {
          const s = spring({frame: f - i * 2.2, fps, config: {damping: 18, stiffness: 140}});
          return (
            <span key={i} style={{display: 'inline-block', marginRight: 22, opacity: s, transform: `translateY(${(1 - s) * 30}px)`}}>
              {w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* Short kinetic word laid over footage (e.g. "Iqtisodiyot?"). */
export const OverlayWord: React.FC<{text: string}> = ({text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 14, stiffness: 160}});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', background: 'rgba(7,16,31,0.35)'}}>
      <div
        style={{
          fontFamily: HEAD,
          fontWeight: 800,
          fontSize: 120,
          color: C.ink,
          transform: `scale(${0.85 + 0.15 * s})`,
          opacity: s,
          textShadow: '0 8px 40px rgba(0,0,0,0.6)',
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

export const fadeIn = (f: number, n = 8) =>
  interpolate(f, [0, n], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

export const sec = (s: number) => Math.round(s * FPS);
