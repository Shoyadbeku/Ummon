import '@fontsource/montserrat/600.css';
import '@fontsource/montserrat/800.css';
import '@fontsource/montserrat/900.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/700.css';
import {spring, interpolate, Easing} from 'remotion';

export const FPS = 30;
export const AUDIO_END = 614.47;
export const TOTAL_FRAMES = Math.ceil(AUDIO_END * FPS);

export const C = {
  bg: '#06080e',
  ink: '#ffffff',
  gold: '#FFC83D',
  red: '#FF3D3D',
  cyan: '#3DDCFF',
  green: '#3DFF8C',
  dim: 'rgba(255,255,255,0.62)',
  glass: 'rgba(12,16,26,0.62)',
};
export const HEAD = 'Montserrat, sans-serif';
export const BODY = 'Inter, sans-serif';

// spring that starts at frame `at`
export const pop = (frame: number, at = 0, damping = 13, stiffness = 140, mass = 0.8) =>
  spring({frame: frame - at, fps: FPS, config: {damping, stiffness, mass}});

export const ease = (frame: number, a: number, b: number, from = 0, to = 1, e = Easing.bezier(0.16, 1, 0.3, 1)) =>
  interpolate(frame, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});

export const sec = (s: number) => Math.round(s * FPS);

export const textStroke = (px = 6, color = '#000') => ({
  WebkitTextStroke: `${px}px ${color}`,
  paintOrder: 'stroke fill' as const,
});
