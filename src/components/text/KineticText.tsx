import React from 'react';
import {interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp} from '../../lib/anim';
import {COLORS, FONT_DISPLAY, GRADIENT_TEXT} from '../../lib/theme';

export type KineticMode = 'rise' | 'pop' | 'slam' | 'type';

type Props = {
  text: string;
  /** Birinchi so'z chiqadigan kadr */
  start: number;
  /** So'zlar shu oraliq ichida tarqalib chiqadi (nutq davomiyligi) */
  duration: number;
  highlight?: string[];
  accent?: string;
  accent2?: string;
  fontSize?: number;
  fontWeight?: number;
  color?: string;
  align?: 'left' | 'center' | 'right';
  mode?: KineticMode;
  lineHeight?: number;
  maxWidth?: number;
  uppercase?: boolean;
  letterSpacing?: number;
  style?: React.CSSProperties;
};

/**
 * Kinetik tipografiya: har bir so'z spring fizikasi bilan
 * (pozitsiya, masshtab, shaffoflik, xiralik) nutq ritmiga mos ravishda chiqadi.
 */
export const KineticText: React.FC<Props> = ({
  text,
  start,
  duration,
  highlight = [],
  accent = COLORS.saffron,
  accent2 = '#FDE68A',
  fontSize = 84,
  fontWeight = 800,
  color = COLORS.text,
  align = 'left',
  mode = 'rise',
  lineHeight = 1.12,
  maxWidth,
  uppercase = false,
  letterSpacing = -1,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(' ').filter(Boolean);
  const totalChars = text.length;

  let charCursor = 0;
  return (
    <div
      style={{
        fontFamily: FONT_DISPLAY,
        fontSize,
        fontWeight,
        color,
        lineHeight,
        textAlign: align,
        maxWidth,
        letterSpacing,
        textTransform: uppercase ? 'uppercase' : undefined,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start',
        columnGap: fontSize * 0.26,
        ...style,
      }}
    >
      {words.map((word, i) => {
        const appearAt = start + (charCursor / Math.max(1, totalChars)) * duration * 0.92;
        charCursor += word.length + 1;
        const isHi = highlight.includes(word);
        return (
          <Word
            key={i}
            word={word}
            appearAt={appearAt}
            fps={fps}
            frame={frame}
            mode={mode}
            seed={i}
            highlight={isHi}
            accent={accent}
            accent2={accent2}
            fontSize={fontSize}
          />
        );
      })}
    </div>
  );
};

const Word: React.FC<{
  word: string;
  appearAt: number;
  fps: number;
  frame: number;
  mode: KineticMode;
  seed: number;
  highlight: boolean;
  accent: string;
  accent2: string;
  fontSize: number;
}> = ({word, appearAt, fps, frame, mode, seed, highlight, accent, accent2, fontSize}) => {
  const local = frame - appearAt;
  const cfg =
    mode === 'slam'
      ? {damping: 11, stiffness: 260, mass: 0.9}
      : mode === 'pop'
        ? {damping: 10, stiffness: 190, mass: 0.6}
        : {damping: 16, stiffness: 150, mass: 0.7};
  const s = spring({frame: local, fps, config: cfg});
  const opacity = interpolate(local, [0, 8], [0, 1], clamp);

  const tilt = (random(`tilt-${seed}-${word}`) - 0.5) * 14;
  let transform = '';
  if (mode === 'rise') {
    transform = `translateY(${(1 - s) * fontSize * 0.7}px) scale(${0.75 + 0.25 * s}) rotate(${(1 - s) * tilt}deg)`;
  } else if (mode === 'pop') {
    transform = `scale(${s}) rotate(${(1 - s) * tilt * 2}deg)`;
  } else if (mode === 'slam') {
    transform = `scale(${interpolate(s, [0, 1], [2.6, 1])}) translateY(${(1 - s) * -30}px)`;
  } else {
    transform = `translateX(${(1 - s) * 24}px)`;
  }
  const blur = Math.max(0, (1 - s) * (mode === 'slam' ? 14 : 9));

  // Ajratilgan so'z ostidagi animatsion chiziq
  const bar = spring({frame: local - 10, fps, config: {damping: 200, stiffness: 120}});

  return (
    <span
      style={{
        display: 'inline-block',
        position: 'relative',
        opacity,
        transform,
        filter: blur > 0.3 ? `blur(${blur}px)` : undefined,
        whiteSpace: 'nowrap',
        willChange: 'transform',
      }}
    >
      {highlight && (
        <span
          style={{
            position: 'absolute',
            left: -fontSize * 0.08,
            right: -fontSize * 0.08,
            bottom: fontSize * 0.04,
            height: fontSize * 0.2,
            borderRadius: fontSize,
            background: `linear-gradient(90deg, ${accent}, ${accent2})`,
            opacity: 0.35,
            transform: `scaleX(${bar})`,
            transformOrigin: 'left center',
          }}
        />
      )}
      <span style={{position: 'relative', ...(highlight ? GRADIENT_TEXT(accent2, accent) : null)}}>{word}</span>
    </span>
  );
};
