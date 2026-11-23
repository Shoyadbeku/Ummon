import React from 'react';
import {AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

export const FONT = '"Inter", "Helvetica Neue", Arial, sans-serif';
export const SERIF = '"Playfair Display", Georgia, "Times New Roman", serif';
export const ACCENT = '#5fd4ff';
export const WARM = '#ffb547';

export const ease = Easing.bezier(0.33, 0, 0.15, 1);

/** Procedural starfield — original motion graphic used behind data cards */
export const Starfield: React.FC<{seed?: string; drift?: number; tint?: string}> = ({
  seed = 'stars',
  drift = 0.4,
  tint = '#0a1630',
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const stars = React.useMemo(
    () =>
      new Array(260).fill(0).map((_, i) => ({
        x: random(`${seed}x${i}`) * width,
        y: random(`${seed}y${i}`) * height,
        z: 0.2 + random(`${seed}z${i}`) * 0.8,
        tw: random(`${seed}t${i}`) * Math.PI * 2,
      })),
    [seed, width, height],
  );
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 50% 55%, ${tint} 0%, #03060f 60%, #000 100%)`,
      }}
    >
      <svg width={width} height={height}>
        {stars.map((s, i) => {
          const x = (s.x - frame * drift * s.z + width * 4) % width;
          const o = 0.35 + 0.65 * s.z * (0.75 + 0.25 * Math.sin(frame / 18 + s.tw));
          return <circle key={i} cx={x} cy={s.y} r={s.z * 1.7} fill="#fff" opacity={o} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Film grain + vignette + letterbox-ish cinematic grade overlay */
export const CinematicOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 8;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)',
        }}
      />
      <AbsoluteFill style={{opacity: 0.07, mixBlendMode: 'overlay'}}>
        <svg width="100%" height="100%">
          <filter id={`g${seed}`}>
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} />
          </filter>
          <rect width="100%" height="100%" filter={`url(#g${seed})`} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Source attribution tag (bottom-left) */
export const Credit: React.FC<{text?: string; label?: string}> = ({text, label}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!text && !label) return null;
  const p = spring({frame: frame - 6, fps, config: {damping: 200}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 64,
        top: 54,
        opacity: p,
        transform: `translateX(${(1 - p) * -30}px)`,
        fontFamily: FONT,
      }}
    >
      {label ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            color: '#fff',
            fontSize: 30,
            fontWeight: 700,
            letterSpacing: 0.5,
            textShadow: '0 2px 12px rgba(0,0,0,0.8)',
          }}
        >
          <div style={{width: 6, height: 34, background: ACCENT, borderRadius: 3}} />
          {label}
        </div>
      ) : null}
      {text ? (
        <div
          style={{
            marginTop: label ? 8 : 0,
            marginLeft: label ? 20 : 0,
            color: 'rgba(255,255,255,0.72)',
            fontSize: 19,
            fontWeight: 500,
            letterSpacing: 1.2,
            textTransform: 'uppercase',
            textShadow: '0 2px 8px rgba(0,0,0,0.9)',
          }}
        >
          {text}
        </div>
      ) : null}
    </div>
  );
};

export const fadeInOut = (frame: number, dur: number, f = 12) =>
  interpolate(frame, [0, f, dur - f, dur], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
