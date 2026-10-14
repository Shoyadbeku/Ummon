import {Easing, interpolate, spring} from 'remotion';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const popSpring = (frame: number, fps: number, delay = 0, config = {damping: 13, stiffness: 170, mass: 0.7}) =>
  spring({frame: frame - delay, fps, config});

export const softSpring = (frame: number, fps: number, delay = 0) =>
  spring({frame: frame - delay, fps, config: {damping: 200, stiffness: 90, mass: 1}});

export const fadeIn = (frame: number, start: number, len = 20) =>
  interpolate(frame, [start, start + len], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

export const ease = (frame: number, input: [number, number], output: [number, number], easing = Easing.inOut(Easing.cubic)) =>
  interpolate(frame, input, output, {...clamp, easing});

/** Silliq "suzish" harakati (float / hover) */
export const float = (frame: number, amp = 10, speed = 0.03, phase = 0) => Math.sin(frame * speed + phase) * amp;

/** Kamera silkinishi — vaqt bo'yicha so'nuvchi */
export const shake = (frame: number, start: number, len = 24, power = 18) => {
  const t = frame - start;
  if (t < 0 || t > len) return {x: 0, y: 0, r: 0};
  const decay = 1 - t / len;
  return {
    x: Math.sin(t * 2.3) * power * decay,
    y: Math.cos(t * 3.1) * power * 0.6 * decay,
    r: Math.sin(t * 1.7) * 2 * decay,
  };
};
