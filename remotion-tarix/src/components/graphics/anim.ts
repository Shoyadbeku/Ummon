import {Easing, interpolate, spring} from 'remotion';

// Kirish/chiqish uchun umumiy yordamchi: 0 -> 1 -> 0
export const inOut = (frame: number, dur: number, fps: number, inF = 18, outF = 14) => {
  const i = spring({frame, fps, config: {damping: 200}, durationInFrames: inF});
  const o = interpolate(frame, [dur - outF, dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  return Math.min(i, o);
};
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
