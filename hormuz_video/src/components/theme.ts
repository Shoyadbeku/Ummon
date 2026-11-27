import '@fontsource/inter/400.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/800.css';
import '@fontsource/oswald/500.css';
import '@fontsource/oswald/700.css';
import {interpolate, Easing} from 'remotion';

export const C = {
  red: '#E3121B',
  redDark: '#9E0B12',
  amber: '#FFB21A',
  navy: '#0B1422',
  navy2: '#13223A',
  panel: 'rgba(9,16,28,0.86)',
  white: '#FFFFFF',
  grey: '#AEB8C6',
  line: 'rgba(255,255,255,0.18)',
  green: '#2BC48A',
};
export const F = {
  head: 'Oswald, Inter, sans-serif',
  body: 'Inter, sans-serif',
};
export const FPS = 30;
export const ease = Easing.bezier(0.22, 1, 0.36, 1);

/** 0..1 kirish/chiqish animatsiyasi (frame — Sequence ichidagi kadr) */
export const inOut = (frame: number, dur: number, inF = 10, outF = 8) =>
  Math.min(
    interpolate(frame, [0, inF], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}),
    interpolate(frame, [dur - outF, dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad)}),
  );
export const appear = (frame: number, at: number, len = 10) =>
  interpolate(frame, [at, at + len], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
