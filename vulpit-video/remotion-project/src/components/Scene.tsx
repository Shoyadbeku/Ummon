import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {BAND_CY, BAND_H, BAND_TOP, LAYOUT, SceneT} from '../data';

export type TransitionKind = 'fade' | 'black' | 'white' | 'wipe' | 'cut' | 'none';
const IMG_RATIO = 2064 / 1152;
const easeInOut = Easing.bezier(0.45, 0, 0.25, 1);

type Cam = {x: number; y: number; z: number; rot: number; shakeX: number; shakeY: number};

/** Frame-based virtual camera for every motion preset. x/y are the focal point in image space (0..1). */
const camera = (s: SceneT, frame: number, dur: number, fps: number): Cam => {
  const p = easeInOut(Math.min(1, Math.max(0, frame / Math.max(1, dur))));
  const lin = Math.min(1, frame / Math.max(1, dur));
  let x = s.fx, y = s.fy, z = interpolate(p, [0, 1], [s.z0, s.z1]), rot = 0, shakeX = 0, shakeY = 0;
  switch (s.motion) {
    case 'panR': x = s.fx - 0.09 + 0.18 * p; break;
    case 'panL': x = s.fx + 0.09 - 0.18 * p; break;
    case 'tiltUp': y = s.fy + 0.08 - 0.16 * p; break;
    case 'tiltDown': y = s.fy - 0.08 + 0.16 * p; break;
    case 'drift': x = s.fx - 0.03 + 0.06 * lin; y = s.fy + 0.02 - 0.04 * lin; rot = -0.6 + 1.2 * lin; break;
    case 'rotate': rot = interpolate(lin, [0, 1], [-2.5, 2.5]); break;
    case 'slam': {
      const sp = spring({frame, fps, config: {damping: 14, stiffness: 120, mass: 0.9}});
      z = interpolate(sp, [0, 1], [s.z0, s.z1 + 0.08]) + 0.1 * lin; // then keeps creeping in
      break;
    }
    case 'punch': {
      const sp = spring({frame, fps, config: {damping: 12, stiffness: 200}});
      z = interpolate(sp, [0, 1], [s.z0 + 0.25, s.z0]) + (s.z1 - s.z0) * lin;
      break;
    }
    case 'shake': {
      const amp = 7 * Math.exp(-frame / 40) + 1.2;
      shakeX = (random(`sx${s.id}${Math.floor(frame / 2)}`) - 0.5) * amp;
      shakeY = (random(`sy${s.id}${Math.floor(frame / 2)}`) - 0.5) * amp;
      break;
    }
    default: break;
  }
  return {x, y, z, rot, shakeX, shakeY};
};

export const Scene: React.FC<{scene: SceneT; dur: number; transition: TransitionKind; tr: number}> = ({scene, dur, transition, tr}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cam = camera(scene, frame, dur, fps);

  const L = LAYOUT.landscape;
  const FW = LAYOUT.W, FH = LAYOUT.H;
  // 16:9: the photograph fills the whole frame; pans/tilts need some headroom, so zoom is floored.
  const isPan = ['panL', 'panR', 'tiltUp', 'tiltDown'].includes(scene.motion);
  const z = L ? Math.max(cam.z, isPan ? 1.16 : 1.0) : cam.z;
  const h = (L ? FH : BAND_H) * z;
  const w = h * IMG_RATIO;
  const half = FW / 2 / w;
  const cx = Math.min(1 - half, Math.max(half, cam.x));
  const halfY = FH / 2 / h;
  const cy = L ? Math.min(1 - halfY, Math.max(halfY, cam.y)) : cam.y;
  const left = FW / 2 - cx * w + cam.shakeX;
  const top = (L ? FH / 2 : BAND_CY) - cy * h + cam.shakeY;

  // grading tweaks per motion (story-driven): colour drains, light fades, sun blooms
  let filter = '';
  if (scene.motion === 'desat') filter = `saturate(${interpolate(frame, [0, dur], [1.05, 0.35], {extrapolateRight: 'clamp'})})`;
  if (scene.motion === 'dim') filter = `brightness(${interpolate(frame, [0, dur], [0.9, 0.45], {extrapolateRight: 'clamp'})}) saturate(0.7)`;
  if (scene.motion === 'flash') filter = `brightness(${interpolate(frame, [0, 25], [1.9, 1], {extrapolateRight: 'clamp'})})`;

  // transitions (incoming side)
  let opacity = 1;
  let clip: string | undefined;
  let tBlur = 0;
  let tScale = 1;
  if (transition === 'fade' || transition === 'white' || transition === 'black') {
    opacity = interpolate(frame, [0, tr], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    tScale = interpolate(frame, [0, tr], [1.035, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
    tBlur = interpolate(frame, [0, tr], [6, 0], {extrapolateRight: 'clamp'});
  } else if (transition === 'wipe') {
    const q = interpolate(frame, [0, tr + 4], [100, 0], {extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
    clip = `polygon(${q}% 0, 100% 0, 100% 100%, ${Math.max(0, q - 12)}% 100%)`;
  }

  // parallax: blurred background drifts against the photograph
  const bgShift = (0.5 - cx) * 90 + cam.shakeX * 0.3;
  const bgScale = 1.18 + 0.06 * Math.min(1, frame / Math.max(1, dur));

  return (
    <AbsoluteFill style={{opacity, clipPath: clip, transform: `scale(${tScale})`, filter: tBlur > 0.3 ? `blur(${tBlur}px)` : undefined}}>
      {L ? (
        <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#05080a'}}>
          <Img
            src={staticFile(scene.image)}
            style={{position: 'absolute', left, top, width: w, height: h, transform: `rotate(${cam.rot}deg) scale(${cam.rot ? 1.04 : 1})`, transformOrigin: `${cx * 100}% ${cy * 100}%`, filter: filter || undefined}}
          />
        </AbsoluteFill>
      ) : (
        <>
          <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#05080a'}}>
            <Img
              src={staticFile(scene.image.replace('images/', 'bg/'))}
              style={{position: 'absolute', width: 1080, height: 1920, objectFit: 'cover', transform: `translateX(${bgShift}px) scale(${bgScale})`, filter: filter || undefined}}
            />
          </AbsoluteFill>
          {/* photograph band with feathered (masked) edges */}
          <div
            style={{
              position: 'absolute', left: 0, top: BAND_TOP - 140, width: 1080, height: BAND_H + 280, overflow: 'hidden',
              WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 16%, black 82%, transparent 100%)',
              maskImage: 'linear-gradient(to bottom, transparent 0%, black 16%, black 82%, transparent 100%)',
            }}
          >
            <Img
              src={staticFile(scene.image)}
              style={{
                position: 'absolute', left, top: top - (BAND_TOP - 140), width: w, height: h,
                transform: `rotate(${cam.rot}deg)`, transformOrigin: `${cx * 100}% ${cam.y * 100}%`, filter: filter || undefined,
              }}
            />
          </div>
        </>
      )}
      {scene.motion === 'flash' ? (
        <AbsoluteFill style={{background: 'radial-gradient(circle at 40% 42%, rgba(255,244,214,1) 0%, rgba(255,214,140,0.6) 35%, rgba(255,200,120,0) 70%)', opacity: interpolate(frame, [0, 6, 40], [0, 1, 0], {extrapolateRight: 'clamp'}), mixBlendMode: 'screen'}} />
      ) : null}
      {transition === 'white' ? (
        <AbsoluteFill style={{backgroundColor: '#fff6e6', opacity: interpolate(frame, [0, 3, tr + 6], [0, 0.85, 0], {extrapolateRight: 'clamp'})}} />
      ) : null}
    </AbsoluteFill>
  );
};

/** Outgoing side of a "dip to black" transition is drawn by the incoming scene's black layer. */
export const DipBlack: React.FC<{tr: number}> = ({tr}) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{backgroundColor: '#000', opacity: interpolate(frame, [0, tr * 0.6, tr * 1.6], [0, 1, 0], {extrapolateRight: 'clamp'})}} />;
};
