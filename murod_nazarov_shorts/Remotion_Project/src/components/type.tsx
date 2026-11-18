import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, spring} from 'remotion';
import {C, FONT_DISPLAY, FONT_SERIF, FONT_UI, ease, useSec} from './core';

const textShadow = '0 6px 30px rgba(0,0,0,0.55), 0 2px 6px rgba(0,0,0,0.5)';

/** Words appear one by one at given local seconds: rise + de-blur + spring scale. */
export const KineticLine: React.FC<{
  words: Array<{t: string; at: number; color?: string}>;
  size?: number;
  weight?: number;
  font?: string;
  italic?: boolean;
  gap?: number;
  align?: 'center' | 'left';
  tracking?: number;
}> = ({words, size = 120, weight = 900, font = FONT_DISPLAY, italic = false, gap = 0.28, align = 'center', tracking = -2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: align === 'center' ? 'center' : 'flex-start',
        columnGap: size * gap,
        rowGap: size * 0.05,
        lineHeight: 1.0,
      }}
    >
      {words.map((w, i) => {
        const s = spring({frame: frame - Math.round(w.at * fps), fps, config: {damping: 13, stiffness: 160, mass: 0.6}});
        const p = interpolate(frame - w.at * fps, [0, 7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              fontFamily: font,
              fontWeight: weight,
              fontStyle: italic ? 'italic' : 'normal',
              fontSize: size,
              letterSpacing: tracking,
              color: w.color ?? C.white,
              textShadow,
              opacity: p,
              transform: `translateY(${(1 - s) * size * 0.6}px) scale(${0.7 + 0.3 * s})`,
              filter: `blur(${(1 - p) * 12}px)`,
            }}
          >
            {w.t}
          </span>
        );
      })}
    </div>
  );
};

/** Big slam word: scales down from huge with overshoot + letter tracking release. */
export const Slam: React.FC<{text: string; at: number; size?: number; color?: string; font?: string; italic?: boolean; stroke?: boolean}> = ({
  text,
  at,
  size = 190,
  color = C.white,
  font = FONT_DISPLAY,
  italic = false,
  stroke = false,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - Math.round(at * fps), fps, config: {damping: 11, stiffness: 180, mass: 0.8}});
  const o = interpolate(frame - at * fps, [0, 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tracking = interpolate(s, [0, 1], [40, -4]);
  return (
    <div
      style={{
        fontFamily: font,
        fontWeight: 900,
        fontStyle: italic ? 'italic' : 'normal',
        fontSize: size,
        lineHeight: 0.95,
        letterSpacing: tracking,
        color: stroke ? 'transparent' : color,
        WebkitTextStroke: stroke ? `4px ${color}` : undefined,
        textShadow: stroke ? undefined : textShadow,
        transform: `scale(${interpolate(s, [0, 1], [2.4, 1])})`,
        opacity: o,
        filter: `blur(${(1 - Math.min(1, s)) * 10}px)`,
        textAlign: 'center',
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </div>
  );
};

/** Text that reveals letter by letter behind a moving mask (clip-path wipe). */
export const WipeText: React.FC<{text: string; at: number; dur?: number; size?: number; color?: string; font?: string; weight?: number; italic?: boolean; tracking?: number}> = ({
  text,
  at,
  dur = 0.45,
  size = 110,
  color = C.white,
  font = FONT_DISPLAY,
  weight = 900,
  italic = false,
  tracking = 0,
}) => {
  const t = useSec();
  const p = interpolate(t, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <div
      style={{
        fontFamily: font,
        fontWeight: weight,
        fontStyle: italic ? 'italic' : 'normal',
        fontSize: size,
        letterSpacing: tracking,
        color,
        lineHeight: 1.0,
        textShadow,
        clipPath: `inset(-20% ${100 - p * 100}% -20% 0)`,
        transform: `translateX(${(1 - p) * -30}px)`,
        whiteSpace: 'nowrap',
      }}
    >
      {text}
    </div>
  );
};

/** Animated number counter. */
export const Counter: React.FC<{from: number; to: number; at: number; dur: number; size?: number; color?: string; font?: string; pad?: number}> = ({
  from,
  to,
  at,
  dur,
  size = 260,
  color = C.white,
  font = FONT_DISPLAY,
  pad = 0,
}) => {
  const t = useSec();
  const p = interpolate(t, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const v = Math.round(from + (to - from) * p);
  const landed = t >= at + dur;
  const pop = interpolate(t, [at + dur, at + dur + 0.12, at + dur + 0.3], [1, 1.08, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o = interpolate(t, [at - 0.1, at + 0.05], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        fontFamily: font,
        fontWeight: 900,
        fontSize: size,
        lineHeight: 0.9,
        color,
        letterSpacing: -6,
        fontVariantNumeric: 'tabular-nums',
        textShadow: landed ? `0 0 60px ${color}66, 0 8px 40px rgba(0,0,0,0.6)` : textShadow,
        transform: `scale(${pop})`,
        opacity: o,
        filter: landed ? 'none' : `blur(${(1 - p) * 4}px)`,
      }}
    >
      {String(v).padStart(pad, '0')}
    </div>
  );
};

/** Small pill label, used as a "chapter" tag. */
export const Chip: React.FC<{text: string; at: number; color?: string; dark?: boolean}> = ({text, at, color = C.accent, dark = true}) => {
  const t = useSec();
  const p = interpolate(t, [at, at + 0.35], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 28px',
        borderRadius: 999,
        background: dark ? 'rgba(10,12,18,0.72)' : color,
        border: `2px solid ${color}`,
        backdropFilter: 'blur(10px)',
        fontFamily: FONT_UI,
        fontWeight: 700,
        fontSize: 34,
        letterSpacing: 4,
        color: dark ? color : '#111',
        textTransform: 'uppercase',
        opacity: p,
        transform: `translateY(${(1 - p) * 30}px)`,
        clipPath: `inset(0 ${100 - p * 100}% 0 0 round 999px)`,
      }}
    >
      <span style={{width: 14, height: 14, borderRadius: 7, background: color, display: 'inline-block'}} />
      {text}
    </div>
  );
};

/** Animated underline / accent bar that grows from left. */
export const Bar: React.FC<{at: number; width?: number; color?: string; height?: number; dur?: number}> = ({at, width = 420, color = C.accent, height = 10, dur = 0.4}) => {
  const t = useSec();
  const p = interpolate(t, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return <div style={{width: width * p, height, background: color, borderRadius: height, boxShadow: `0 0 30px ${color}88`}} />;
};

export const Serif: React.FC<{children: React.ReactNode; size?: number; color?: string}> = ({children, size = 64, color = C.white}) => (
  <div style={{fontFamily: FONT_SERIF, fontStyle: 'italic', fontWeight: 700, fontSize: size, color, textShadow, lineHeight: 1.1}}>{children}</div>
);

/** Safe-zone layout helper: content block centred vertically between y=top..bottom. */
export const Safe: React.FC<{children: React.ReactNode; top?: number; bottom?: number; justify?: 'center' | 'flex-start' | 'flex-end'; align?: 'center' | 'flex-start'}> = ({
  children,
  top = 300,
  bottom = 480,
  justify = 'center',
  align = 'center',
}) => (
  <AbsoluteFill
    style={{
      paddingTop: top,
      paddingBottom: bottom,
      paddingLeft: 80,
      paddingRight: 110,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: justify,
      alignItems: align,
      textAlign: align === 'center' ? 'center' : 'left',
      gap: 24,
    }}
  >
    {children}
  </AbsoluteFill>
);

/** Darkening gradient behind text for legibility. */
export const Scrim: React.FC<{from?: 'bottom' | 'top' | 'center'; strength?: number}> = ({from = 'center', strength = 0.55}) => {
  const bg =
    from === 'bottom'
      ? `linear-gradient(0deg, rgba(0,0,0,${strength + 0.2}) 0%, rgba(0,0,0,${strength}) 35%, rgba(0,0,0,0) 70%)`
      : from === 'top'
        ? `linear-gradient(180deg, rgba(0,0,0,${strength + 0.2}) 0%, rgba(0,0,0,${strength}) 35%, rgba(0,0,0,0) 70%)`
        : `radial-gradient(ellipse 90% 45% at 50% 50%, rgba(0,0,0,${strength}) 0%, rgba(0,0,0,0) 100%)`;
  return <AbsoluteFill style={{background: bg}} />;
};
