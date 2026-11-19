import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import { BODY, C, HEAD } from './fx';

type Anim = 'rise' | 'slam' | 'mask' | 'blur' | 'letters';

/**
 * One kinetic word / line that appears at local frame `at`.
 * - rise:    slides up with spring + motion blur
 * - slam:    scales down from huge with overshoot (impact)
 * - mask:    revealed by a sliding mask (clip-path)
 * - blur:    focus-pull from heavy blur
 * - letters: per-letter staggered spring
 */
export const Word: React.FC<{
  text: string;
  at: number;
  anim?: Anim;
  size?: number;
  color?: string;
  font?: 'head' | 'body';
  stroke?: boolean;
  glow?: string;
  out?: number; // local frame to exit
  letterSpacing?: number;
  style?: React.CSSProperties;
  bg?: string;
}> = ({ text, at, anim = 'rise', size = 150, color = C.white, font = 'head', stroke, glow, out, letterSpacing = 0, style, bg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - at;
  if (local < 0) return null;
  const sp = spring({ frame: local, fps, config: { damping: 14, stiffness: 180, mass: 0.7 } });
  const exit = out !== undefined ? interpolate(frame, [out, out + 6], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0;
  if (exit >= 1) return null;

  let transform = '';
  let filter = '';
  let opacity = 1;
  let clipPath: string | undefined;

  if (anim === 'rise') {
    transform = `translateY(${interpolate(sp, [0, 1], [90, 0])}px)`;
    filter = `blur(${interpolate(sp, [0, 0.7, 1], [14, 2, 0])}px)`;
    opacity = interpolate(sp, [0, 0.4], [0, 1], { extrapolateRight: 'clamp' });
  } else if (anim === 'slam') {
    const s2 = spring({ frame: local, fps, config: { damping: 11, stiffness: 260, mass: 0.6 } });
    transform = `scale(${interpolate(s2, [0, 1], [3.2, 1])})`;
    filter = `blur(${interpolate(s2, [0, 0.6, 1], [18, 1, 0], { extrapolateRight: 'clamp' })}px)`;
    opacity = interpolate(local, [0, 2], [0, 1], { extrapolateRight: 'clamp' });
  } else if (anim === 'mask') {
    const p = interpolate(local, [0, 9], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
    clipPath = `inset(0 ${100 - p * 100}% 0 0)`;
    transform = `translateX(${interpolate(p, [0, 1], [-30, 0])}px)`;
  } else if (anim === 'blur') {
    const p = interpolate(local, [0, 12], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.quad) });
    filter = `blur(${(1 - p) * 30}px)`;
    opacity = p;
    transform = `scale(${interpolate(p, [0, 1], [1.25, 1])})`;
  }

  if (exit > 0) {
    opacity *= 1 - exit;
    transform += ` translateY(${-exit * 40}px)`;
    filter += ` blur(${exit * 12}px)`;
  }

  const base: React.CSSProperties = {
    fontFamily: font === 'head' ? HEAD : BODY,
    fontWeight: font === 'head' ? 400 : 800,
    fontSize: size,
    lineHeight: 0.95,
    color,
    textTransform: 'uppercase',
    letterSpacing,
    textAlign: 'center',
    WebkitTextStroke: stroke ? `3px ${color}` : undefined,
    textShadow: glow ? `0 0 30px ${glow}, 0 0 80px ${glow}` : '0 8px 40px rgba(0,0,0,0.65)',
    display: 'inline-block',
    whiteSpace: 'pre',
    ...style,
  };

  if (anim === 'letters') {
    return (
      <div style={{ ...base, opacity: 1 - exit, background: bg, padding: bg ? '6px 22px' : undefined }}>
        {text.split('').map((ch, i) => {
          const s = spring({ frame: local - i * 1.4, fps, config: { damping: 13, stiffness: 200, mass: 0.6 } });
          return (
            <span
              key={i}
              style={{
                display: 'inline-block',
                transform: `translateY(${interpolate(s, [0, 1], [70, 0])}px) rotate(${interpolate(s, [0, 1], [12, 0])}deg)`,
                opacity: interpolate(s, [0, 0.3], [0, 1], { extrapolateRight: 'clamp' }),
                filter: `blur(${interpolate(s, [0, 1], [8, 0])}px)`,
              }}
            >
              {ch}
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div style={{ ...base, transform, filter, opacity, clipPath, background: bg, padding: bg ? '6px 22px' : undefined }}>
      {text}
    </div>
  );
};

/** Centred stack positioned in the mobile-safe area. */
export const Stack: React.FC<{ top?: number; gap?: number; children: React.ReactNode; align?: 'center' | 'flex-start' }> = ({
  top = 1080,
  gap = 10,
  children,
  align = 'center',
}) => (
  <div
    style={{
      position: 'absolute',
      left: 70,
      right: 70,
      top,
      display: 'flex',
      flexDirection: 'column',
      alignItems: align,
      gap,
    }}
  >
    {children}
  </div>
);

/** Small pill label with animated underline bar. */
export const Tag: React.FC<{ text: string; at: number; color?: string; top?: number; textColor?: string }> = ({
  text,
  at,
  color = C.red,
  top = 300,
  textColor = '#fff',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - at;
  if (local < 0) return null;
  const s = spring({ frame: local, fps, config: { damping: 16, stiffness: 160 } });
  return (
    <div style={{ position: 'absolute', top, left: 0, right: 0, display: 'flex', justifyContent: 'center' }}>
      <div
        style={{
          fontFamily: BODY,
          fontWeight: 800,
          fontSize: 40,
          letterSpacing: 6,
          color: textColor,
          background: color,
          padding: '12px 28px',
          borderRadius: 6,
          textTransform: 'uppercase',
          transform: `scale(${interpolate(s, [0, 1], [0.6, 1])})`,
          opacity: s,
          clipPath: `inset(0 ${(1 - s) * 50}% 0 ${(1 - s) * 50}%)`,
          boxShadow: `0 0 40px ${color}88`,
        }}
      >
        {text}
      </div>
    </div>
  );
};
