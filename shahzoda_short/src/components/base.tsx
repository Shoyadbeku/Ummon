import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FONT} from '../fonts';

export const C = {
  gold: '#FFC83D',
  goldDeep: '#FF9F1C',
  green: '#3DFF8F',
  red: '#FF3B4E',
  accent: '#5EE7FF',
  ink: '#0B0B12',
  white: '#FFFFFF',
};

export const ease = Easing.bezier(0.16, 1, 0.3, 1); // expo-out
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Spring helper relative to a local start frame. */
export const useSpring = (delay = 0, damping = 14, mass = 0.7, stiffness = 160) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: {damping, mass, stiffness}});
};

const GRADE = 'contrast(1.12) saturate(1.12) brightness(0.93)';

type Move = {from: number; to: number; x?: [number, number]; y?: [number, number]};

/** Stock footage, cover-cropped to 9:16, with a Ken Burns move and a cinematic grade. */
export const Clip: React.FC<{
  src: string;
  startFrom?: number; // seconds into the source
  rate?: number;
  pos?: string;
  move?: Move;
  filter?: string;
  dur: number; // local duration in frames, for the move
}> = ({src, startFrom = 0, rate = 1, pos = '50% 50%', move = {from: 1.08, to: 1.2}, filter = '', dur}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, dur], [0, 1], clamp);
  const s = interpolate(p, [0, 1], [move.from, move.to]);
  const x = move.x ? interpolate(p, [0, 1], move.x) : 0;
  const y = move.y ? interpolate(p, [0, 1], move.y) : 0;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <OffthreadVideo
        src={staticFile(`media/video/${src}.mp4`)}
        startFrom={Math.round(startFrom * 30)}
        playbackRate={rate}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: pos,
          transform: `translate(${x}px, ${y}px) scale(${s})`,
          filter: `${GRADE} ${filter}`,
        }}
      />
    </AbsoluteFill>
  );
};

export const Photo: React.FC<{
  src: string;
  pos?: string;
  move?: Move;
  filter?: string;
  dur: number;
  style?: React.CSSProperties;
}> = ({src, pos = '50% 50%', move = {from: 1.05, to: 1.15}, filter = '', dur, style}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, dur], [0, 1], clamp);
  const s = interpolate(p, [0, 1], [move.from, move.to]);
  const x = move.x ? interpolate(p, [0, 1], move.x) : 0;
  const y = move.y ? interpolate(p, [0, 1], move.y) : 0;
  return (
    <AbsoluteFill style={{overflow: 'hidden', ...style}}>
      <Img
        src={staticFile(`media/img/${src}`)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: pos,
          transform: `translate(${x}px, ${y}px) scale(${s})`,
          filter: `${GRADE} ${filter}`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Entrance used at every cut: zoom-whip with motion blur and a short exposure flash. */
export const WhipIn: React.FC<{children: React.ReactNode; strength?: number; dir?: 1 | -1}> = ({
  children,
  strength = 1,
  dir = 1,
}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, 8], [1, 0], {...clamp, easing: ease});
  const scale = 1 + 0.18 * t * strength;
  const blur = 14 * t * strength;
  const y = dir * 60 * t * strength;
  return (
    <AbsoluteFill style={{transform: `translateY(${y}px) scale(${scale})`, filter: blur > 0.3 ? `blur(${blur}px)` : undefined}}>
      {children}
      <AbsoluteFill style={{background: '#fff', opacity: 0.35 * t * strength, mixBlendMode: 'screen'}} />
    </AbsoluteFill>
  );
};

/** Handheld-style shake for a few frames after `at` (local frames). */
export const Shake: React.FC<{at?: number; len?: number; amp?: number; children: React.ReactNode}> = ({
  at = 0,
  len = 10,
  amp = 18,
  children,
}) => {
  const frame = useCurrentFrame();
  const k = interpolate(frame - at, [0, len], [1, 0], clamp);
  const x = (random(`x${frame}`) - 0.5) * 2 * amp * k;
  const y = (random(`y${frame}`) - 0.5) * 2 * amp * k;
  const r = (random(`r${frame}`) - 0.5) * 1.2 * k;
  return <AbsoluteFill style={{transform: `translate(${x}px, ${y}px) rotate(${r}deg)`}}>{children}</AbsoluteFill>;
};

export const Darken: React.FC<{top?: number; bottom?: number; mid?: number}> = ({top = 0.55, bottom = 0.6, mid = 0.15}) => (
  <AbsoluteFill
    style={{
      background: `linear-gradient(180deg, rgba(5,5,12,${top}) 0%, rgba(5,5,12,${mid}) 35%, rgba(5,5,12,${mid}) 55%, rgba(5,5,12,${bottom}) 100%)`,
    }}
  />
);

/** Big kinetic headline: letters rise in with a staggered spring and a soft glow. */
export const Headline: React.FC<{
  text: string;
  delay?: number;
  size?: number;
  color?: string;
  y?: number;
  glow?: string;
  stagger?: number;
  tracking?: number;
}> = ({text, delay = 0, size = 150, color = C.white, y = 300, glow, stagger = 1.6, tracking = -2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const chars = [...text];
  return (
    <div
      style={{
        position: 'absolute',
        top: y,
        left: 0,
        right: 0,
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: size,
        letterSpacing: tracking,
        lineHeight: 1,
        color,
        textShadow: `0 10px 40px rgba(0,0,0,.6)${glow ? `, 0 0 40px ${glow}, 0 0 90px ${glow}` : ''}`,
        whiteSpace: 'pre',
      }}
    >
      {chars.map((ch, i) => {
        const sp = spring({frame: frame - delay - i * stagger, fps, config: {damping: 12, mass: 0.6, stiffness: 180}});
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              transform: `translateY(${(1 - sp) * 90}px) scale(${0.6 + 0.4 * sp})`,
              opacity: Math.min(1, sp * 1.6),
              filter: sp < 0.9 ? `blur(${(1 - sp) * 10}px)` : undefined,
            }}
          >
            {ch}
          </span>
        );
      })}
    </div>
  );
};

/** Small label pill (callout). */
export const Pill: React.FC<{
  text: string;
  delay?: number;
  y: number;
  bg?: string;
  color?: string;
  size?: number;
  icon?: React.ReactNode;
}> = ({text, delay = 0, y, bg = C.gold, color = C.ink, size = 44, icon}) => {
  const sp = useSpring(delay, 13, 0.6, 200);
  return (
    <div style={{position: 'absolute', top: y, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: `${size * 0.32}px ${size * 0.7}px`,
          background: bg,
          color,
          borderRadius: 999,
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: size,
          letterSpacing: 1,
          transform: `scale(${sp}) rotate(${(1 - sp) * -6}deg)`,
          opacity: Math.min(1, sp * 2),
          boxShadow: '0 18px 50px rgba(0,0,0,.45)',
        }}
      >
        {icon}
        {text}
      </div>
    </div>
  );
};

/** Floating light particles / bokeh. */
export const Particles: React.FC<{n?: number; color?: string; seed?: string; speed?: number}> = ({
  n = 26,
  color = C.gold,
  seed = 'p',
  speed = 1,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen'}}>
      {new Array(n).fill(0).map((_, i) => {
        const x = random(`${seed}x${i}`) * 1080;
        const y0 = random(`${seed}y${i}`) * 1920;
        const r = 3 + random(`${seed}r${i}`) * 9;
        const v = (0.6 + random(`${seed}v${i}`) * 1.8) * speed;
        const y = (((y0 - frame * v * 2) % 1920) + 1920) % 1920;
        const tw = 0.35 + 0.65 * Math.abs(Math.sin(frame / (12 + i) + i));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x + Math.sin(frame / 30 + i) * 14,
              top: y,
              width: r * 2,
              height: r * 2,
              borderRadius: '50%',
              background: color,
              opacity: tw * 0.75,
              filter: `blur(${r > 8 ? 4 : 1}px)`,
              boxShadow: `0 0 ${r * 3}px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const Check: React.FC<{size?: number; color?: string; progress: number}> = ({size = 90, color = C.green, progress}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="46" fill={color} opacity={Math.min(1, progress * 2)} />
    <path d="M28 52 L44 67 L73 36" fill="none" stroke={C.ink} strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
  </svg>
);

export const Cross: React.FC<{size?: number; color?: string; progress: number}> = ({size = 90, color = C.red, progress}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="46" fill={color} opacity={Math.min(1, progress * 2)} />
    <path d="M32 32 L68 68 M68 32 L32 68" fill="none" stroke="#fff" strokeWidth="11" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
  </svg>
);
