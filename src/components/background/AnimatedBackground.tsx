import React, {useMemo} from 'react';
import {AbsoluteFill, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS} from '../../lib/theme';

/**
 * Global fon: gradient "mesh" bloblar, perspektivali texno-to'r,
 * parallaks qatlamli abstrakt shakllar, vinyetka va don (grain).
 * Sahnalar ustidan o'tsa ham uzluksiz harakatlanadi.
 */
export const AnimatedBackground: React.FC<{accent: string}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  const blobs = [
    {color: accent, size: 1300, x: 0.18, y: 0.25, sx: 0.0061, sy: 0.0049, ax: 220, ay: 140, o: 0.55},
    {color: COLORS.violet, size: 1150, x: 0.85, y: 0.2, sx: 0.0043, sy: 0.0067, ax: 180, ay: 160, o: 0.42},
    {color: COLORS.cyan, size: 1000, x: 0.7, y: 0.95, sx: 0.0052, sy: 0.0038, ax: 240, ay: 120, o: 0.3},
    {color: accent, size: 900, x: 0.05, y: 1.0, sx: 0.0035, sy: 0.0058, ax: 160, ay: 120, o: 0.28},
  ];

  return (
    <AbsoluteFill style={{backgroundColor: COLORS.bg0, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{background: `linear-gradient(160deg, ${COLORS.bg1} 0%, ${COLORS.bg0} 55%, #05060D 100%)`}}
      />
      {blobs.map((b, i) => {
        const cx = b.x * width + Math.sin(frame * b.sx + i) * b.ax;
        const cy = b.y * height + Math.cos(frame * b.sy + i * 2) * b.ay;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cx - b.size / 2,
              top: cy - b.size / 2,
              width: b.size,
              height: b.size,
              borderRadius: '50%',
              background: `radial-gradient(circle at center, ${b.color} 0%, transparent 62%)`,
              opacity: b.o,
              mixBlendMode: 'screen',
            }}
          />
        );
      })}
      <TechGrid />
      <FloatingShapes accent={accent} />
      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.65) 100%)',
        }}
      />
      <Grain />
    </AbsoluteFill>
  );
};

const TechGrid: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = (frame * 1.6) % 80;
  return (
    <AbsoluteFill style={{perspective: 900, perspectiveOrigin: '50% 30%'}}>
      <div
        style={{
          position: 'absolute',
          left: '-50%',
          width: '200%',
          bottom: -260,
          height: 900,
          transform: 'rotateX(74deg)',
          transformOrigin: '50% 100%',
          backgroundImage:
            'linear-gradient(rgba(148,163,184,0.16) 2px, transparent 2px), linear-gradient(90deg, rgba(148,163,184,0.16) 2px, transparent 2px)',
          backgroundSize: '80px 80px',
          backgroundPosition: `0px ${offset}px`,
          maskImage: 'linear-gradient(to top, black 0%, transparent 85%)',
          WebkitMaskImage: 'linear-gradient(to top, black 0%, transparent 85%)',
        }}
      />
    </AbsoluteFill>
  );
};

type ShapeKind = 'ring' | 'plus' | 'tri' | 'pill' | 'dots' | 'grain';

const FloatingShapes: React.FC<{accent: string}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  const shapes = useMemo(() => {
    const kinds: ShapeKind[] = ['ring', 'plus', 'tri', 'pill', 'dots', 'grain'];
    return new Array(18).fill(0).map((_, i) => ({
      kind: kinds[i % kinds.length],
      x: random(`sx${i}`) * width,
      y: random(`sy${i}`) * height,
      depth: 0.25 + random(`sd${i}`) * 0.75,
      size: 30 + random(`ss${i}`) * 70,
      rot: random(`sr${i}`) * 360,
      spin: (random(`sp${i}`) - 0.5) * 0.8,
      phase: random(`ph${i}`) * Math.PI * 2,
      useAccent: random(`ua${i}`) > 0.5,
    }));
  }, [width, height]);

  return (
    <AbsoluteFill>
      {shapes.map((s, i) => {
        // Parallaks: chuqurroq (depth katta) shakllar tezroq va kattaroq harakatlanadi
        const span = width + 300;
        const x = ((((s.x - frame * 0.9 * s.depth) % span) + span) % span) - 150;
        const y = s.y + Math.sin(frame * 0.012 + s.phase) * 40 * s.depth;
        const color = s.useAccent ? accent : 'rgba(226,232,240,0.9)';
        const size = s.size * s.depth;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              opacity: 0.12 + s.depth * 0.28,
              transform: `rotate(${s.rot + frame * s.spin}deg)`,
            }}
          >
            <Shape kind={s.kind} color={color} size={size} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Shape: React.FC<{kind: ShapeKind; color: string; size: number}> = ({kind, color, size}) => {
  const sw = Math.max(2, size * 0.08);
  switch (kind) {
    case 'ring':
      return <div style={{width: size, height: size, borderRadius: '50%', border: `${sw}px solid ${color}`}} />;
    case 'plus':
      return (
        <svg width={size} height={size} viewBox="0 0 10 10">
          <path d="M5 1v8M1 5h8" stroke={color} strokeWidth={1.4} strokeLinecap="round" />
        </svg>
      );
    case 'tri':
      return (
        <svg width={size} height={size} viewBox="0 0 10 10">
          <path d="M5 1L9 9H1Z" fill="none" stroke={color} strokeWidth={1} strokeLinejoin="round" />
        </svg>
      );
    case 'pill':
      return (
        <div
          style={{
            width: size,
            height: size * 0.36,
            borderRadius: size,
            background: `linear-gradient(90deg, ${color}, transparent)`,
          }}
        />
      );
    case 'dots':
      return (
        <div
          style={{
            width: size,
            height: size,
            backgroundImage: `radial-gradient(${color} 18%, transparent 20%)`,
            backgroundSize: `${size / 4}px ${size / 4}px`,
          }}
        />
      );
    default:
      return (
        <svg width={size} height={size} viewBox="0 0 10 10">
          <ellipse cx={5} cy={5} rx={4.5} ry={1.6} fill={color} />
        </svg>
      );
  }
};

const NOISE = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.55 0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>',
)}")`;

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  // Donni har 2 kadrda siljitib, "jonli plyonka" effekti
  const step = Math.floor(frame / 2);
  const ox = Math.floor(random(`gx${step}`) * 240);
  const oy = Math.floor(random(`gy${step}`) * 240);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: NOISE,
        backgroundPosition: `${ox}px ${oy}px`,
        opacity: 0.06,
        mixBlendMode: 'overlay',
      }}
    />
  );
};
