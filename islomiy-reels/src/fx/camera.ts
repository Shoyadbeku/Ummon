import {Easing, interpolate, random, spring} from 'remotion';
import type {Move} from '../types';

const ease = Easing.bezier(0.45, 0.05, 0.35, 1);

/** Cinematic camera move over the whole shot (frame = local frame, dur = shot length in frames). */
export const cameraTransform = (mv: Move, frame: number, dur: number, fps: number, seed: string) => {
  const p = ease(Math.min(1, Math.max(0, frame / Math.max(1, dur))));
  const lerp = (a: number, b: number) => a + (b - a) * p;
  let s = 1.08;
  let x = 0;
  let y = 0;
  let r = 0;
  const dir = random(seed) > 0.5 ? 1 : -1;
  switch (mv) {
    case 'pushIn':
      s = lerp(1.04, 1.17);
      x = lerp(0, dir * 1.2);
      break;
    case 'pullOut':
      s = lerp(1.18, 1.04);
      break;
    case 'panL':
      s = 1.16;
      x = lerp(4.5, -4.5);
      break;
    case 'panR':
      s = 1.16;
      x = lerp(-4.5, 4.5);
      break;
    case 'rise':
      s = lerp(1.12, 1.15);
      y = lerp(3.5, -3.5);
      break;
    case 'sink':
      s = lerp(1.12, 1.2);
      y = lerp(-3, 3);
      break;
    case 'drift':
      s = lerp(1.06, 1.12);
      x = lerp(-dir * 1.8, dir * 1.8);
      r = lerp(-dir * 0.4, dir * 0.4);
      break;
    case 'punch': {
      const sp = spring({frame, fps, config: {damping: 14, mass: 0.7, stiffness: 120}});
      s = interpolate(sp, [0, 1], [1.42, 1.08]) + p * 0.08;
      break;
    }
  }
  return `translate(${x}%, ${y}%) scale(${s}) rotate(${r}deg)`;
};

/** Earthquake style shake with decaying amplitude, deterministic per frame. */
export const shake = (frame: number, seed: string, amp: number, decayFrames: number) => {
  const k = Math.max(0, 1 - frame / decayFrames);
  const a = amp * k * k;
  const x = (random(`${seed}x${frame}`) - 0.5) * 2 * a;
  const y = (random(`${seed}y${frame}`) - 0.5) * 2 * a;
  const r = (random(`${seed}r${frame}`) - 0.5) * 0.6 * k;
  return `translate(${x}px, ${y}px) rotate(${r}deg)`;
};
