import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const C = {
  bg: '#07090d',
  white: '#ffffff',
  accent: '#ffb547', // warm amber – "building / gold"
  accent2: '#ff5a3c', // Japan red-orange
  cool: '#5fd0ff',
  dim: 'rgba(255,255,255,0.72)',
};

export const FONT_DISPLAY = 'Mont, sans-serif';
export const FONT_SERIF = 'Playfair, serif';
export const FONT_UI = 'InterUI, sans-serif';

export const Fonts: React.FC = () => (
  <style>{`
  @font-face{font-family:Mont;font-weight:600;src:url(${staticFile('fonts/montserrat-latin-600-normal.woff2')}) format('woff2');}
  @font-face{font-family:Mont;font-weight:800;src:url(${staticFile('fonts/montserrat-latin-800-normal.woff2')}) format('woff2');}
  @font-face{font-family:Mont;font-weight:900;src:url(${staticFile('fonts/montserrat-latin-900-normal.woff2')}) format('woff2');}
  @font-face{font-family:Mont;font-weight:900;font-style:italic;src:url(${staticFile('fonts/montserrat-latin-900-italic.woff2')}) format('woff2');}
  @font-face{font-family:Playfair;font-weight:700;font-style:italic;src:url(${staticFile('fonts/playfair-display-latin-700-italic.woff2')}) format('woff2');}
  @font-face{font-family:Playfair;font-weight:900;font-style:italic;src:url(${staticFile('fonts/playfair-display-latin-900-italic.woff2')}) format('woff2');}
  @font-face{font-family:Playfair;font-weight:900;src:url(${staticFile('fonts/playfair-display-latin-900-normal.woff2')}) format('woff2');}
  @font-face{font-family:InterUI;font-weight:500;src:url(${staticFile('fonts/inter-latin-500-normal.woff2')}) format('woff2');}
  @font-face{font-family:InterUI;font-weight:700;src:url(${staticFile('fonts/inter-latin-700-normal.woff2')}) format('woff2');}
  `}</style>
);

export const ease = Easing.bezier(0.16, 1, 0.3, 1); // expo-out
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

export const useSec = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps;
};

/** Spring that starts at local second `at`. */
export const useSpringAt = (at: number, config = {damping: 14, stiffness: 140, mass: 0.7}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - Math.round(at * fps), fps, config});
};

export type Grade = 'cine' | 'warm' | 'cold' | 'vintage' | 'mono' | 'night';

const gradeFilter: Record<Grade, string> = {
  cine: 'contrast(1.12) saturate(1.08) brightness(0.96)',
  warm: 'contrast(1.1) saturate(1.15) sepia(0.12) brightness(0.98)',
  cold: 'contrast(1.12) saturate(0.95) hue-rotate(-6deg) brightness(0.95)',
  vintage: 'sepia(0.65) contrast(1.15) saturate(0.7) brightness(0.9)',
  mono: 'grayscale(0.85) contrast(1.15) brightness(0.92)',
  night: 'contrast(1.15) saturate(1.25) brightness(1.0)',
};

/** Teal/orange split-tone + vignette, applied over footage. */
export const ColorGrade: React.FC<{grade?: Grade; vignette?: number}> = ({grade = 'cine', vignette = 0.75}) => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    {grade !== 'mono' && grade !== 'vintage' ? (
      <AbsoluteFill
        style={{
          background: 'linear-gradient(180deg, rgba(0,70,90,0.22) 0%, rgba(0,0,0,0) 45%, rgba(255,140,40,0.12) 100%)',
          mixBlendMode: 'soft-light',
        }}
      />
    ) : null}
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,${vignette}) 100%)`,
      }}
    />
  </AbsoluteFill>
);

type MoveProps = {
  zoom?: [number, number];
  panX?: [number, number]; // percent translate
  panY?: [number, number];
  rotate?: [number, number];
  grade?: Grade;
  duration: number; // seconds of the scene (for move normalisation)
};

const useMove = ({zoom = [1.04, 1.14], panX = [0, 0], panY = [0, 0], rotate = [0, 0], duration}: MoveProps) => {
  const t = useSec();
  const p = interpolate(t, [0, duration], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: easeInOut});
  const s = interpolate(p, [0, 1], zoom);
  const x = interpolate(p, [0, 1], panX);
  const y = interpolate(p, [0, 1], panY);
  const r = interpolate(p, [0, 1], rotate);
  return `translate(${x}%, ${y}%) scale(${s}) rotate(${r}deg)`;
};

/** Pre-cropped 9:16 clip (public/clips) with camera move and grade. */
export const Clip: React.FC<MoveProps & {src: string; startFrom?: number; rate?: number}> = ({src, startFrom = 0, rate = 1, grade = 'cine', ...move}) => {
  const transform = useMove(move);
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: C.bg}}>
      <AbsoluteFill style={{transform, filter: gradeFilter[grade]}}>
        <OffthreadVideo
          src={staticFile(`clips/${src}.mp4`)}
          startFrom={Math.round(startFrom * fps)}
          playbackRate={rate}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
        />
      </AbsoluteFill>
      <ColorGrade grade={grade} />
    </AbsoluteFill>
  );
};

/** Still photo with Ken Burns / parallax move. focusX picks the horizontal crop (0..100). */
export const Still: React.FC<MoveProps & {src: string; focusX?: number; blurBg?: boolean}> = ({src, focusX = 50, grade = 'cine', blurBg = false, ...move}) => {
  const transform = useMove(move);
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: C.bg}}>
      {blurBg ? (
        <AbsoluteFill style={{filter: 'blur(40px) brightness(0.5)', transform: 'scale(1.2)'}}>
          <Img src={staticFile(`img/${src}`)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{transform, filter: gradeFilter[grade]}}>
        <Img
          src={staticFile(`img/${src}`)}
          style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: `${focusX}% 50%`}}
        />
      </AbsoluteFill>
      <ColorGrade grade={grade} />
    </AbsoluteFill>
  );
};

/** Scene entrance: punch-in zoom with directional motion blur, or whip pan. */
export const Enter: React.FC<{type?: 'punch' | 'whip' | 'whipUp' | 'fade' | 'none'; children: React.ReactNode; frames?: number}> = ({
  type = 'punch',
  children,
  frames = 7,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp', easing: ease});
  let transform = 'none';
  let filter = 'none';
  let opacity = 1;
  if (type === 'punch') {
    transform = `scale(${interpolate(p, [0, 1], [1.28, 1])})`;
    filter = `blur(${interpolate(p, [0, 1], [14, 0])}px) brightness(${interpolate(p, [0, 1], [1.6, 1])})`;
  } else if (type === 'whip') {
    transform = `translateX(${interpolate(p, [0, 1], [38, 0])}%) skewX(${interpolate(p, [0, 1], [-8, 0])}deg)`;
    filter = `blur(${interpolate(p, [0, 1], [24, 0])}px)`;
  } else if (type === 'whipUp') {
    transform = `translateY(${interpolate(p, [0, 1], [30, 0])}%)`;
    filter = `blur(${interpolate(p, [0, 1], [22, 0])}px)`;
  } else if (type === 'fade') {
    opacity = interpolate(frame, [0, frames], [0, 1], {extrapolateRight: 'clamp'});
  }
  return <AbsoluteFill style={{transform, filter: frame > frames ? 'none' : filter, opacity}}>{children}</AbsoluteFill>;
};

/** Film grain: animated SVG turbulence. */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.09}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity, mixBlendMode: 'overlay', pointerEvents: 'none'}}>
      <svg width="100%" height="100%">
        <filter id={`g${frame}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={frame % 30} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#g${frame})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Warm light leak sweeping across the frame, centred on second `at`. */
export const LightLeak: React.FC<{at: number; dur?: number; color?: string}> = ({at, dur = 0.7, color = '255,170,80'}) => {
  const t = useSec();
  const p = interpolate(t, [at - dur / 2, at + dur / 2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (p <= 0 || p >= 1) return null;
  const o = Math.sin(p * Math.PI);
  return (
    <AbsoluteFill
      style={{
        mixBlendMode: 'screen',
        opacity: o * 0.85,
        background: `radial-gradient(ellipse 70% 45% at ${interpolate(p, [0, 1], [-10, 110])}% ${interpolate(p, [0, 1], [20, 70])}%, rgba(${color},0.95), rgba(${color},0) 70%)`,
      }}
    />
  );
};

export const Flash: React.FC<{at: number; dur?: number; color?: string; max?: number}> = ({at, dur = 0.25, color = '#fff', max = 0.9}) => {
  const t = useSec();
  const o = interpolate(t, [at, at + 0.03, at + dur], [0, max, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (o <= 0) return null;
  return <AbsoluteFill style={{backgroundColor: color, opacity: o}} />;
};

/** Camera shake, decaying, starting at local second `at`. */
export const useShake = (at: number, strength = 18, dur = 0.35) => {
  const t = useSec();
  const k = interpolate(t, [at, at + dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (t < at || k <= 0) return 'none';
  const x = Math.sin(t * 97) * strength * k;
  const y = Math.cos(t * 83) * strength * k;
  return `translate(${x}px, ${y}px)`;
};
