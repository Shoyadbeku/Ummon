import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ShotData} from './types';
import {cameraTransform, shake} from './fx/camera';
import {EarthCracks} from './fx/EarthCracks';
import {GoldenKeys} from './fx/GoldenKeys';
import {IslamicPattern} from './fx/IslamicPattern';
import {Glow, LightFlash, LightRays, Lightning, Particles} from './fx/Overlays';
import {VerseBadge} from './fx/VerseBadge';

/** 2.5D parallax for still manuscripts: blurred backplate + floating page + dust in front. */
const ParallaxImage: React.FC<{file: string; mv: ShotData['mv']; dur: number; seed: string}> = ({file, mv, dur, seed}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = Math.min(1, frame / dur);
  const bgT = cameraTransform(mv, frame, dur, fps, seed);
  const fgS = interpolate(p, [0, 1], [mv === 'pullOut' ? 1.1 : 0.98, mv === 'pullOut' ? 0.98 : 1.1]);
  const fgX = mv === 'panL' ? interpolate(p, [0, 1], [3, -3]) : mv === 'panR' ? interpolate(p, [0, 1], [-3, 3]) : 0;
  const fgY = mv === 'rise' ? interpolate(p, [0, 1], [2.5, -2.5]) : mv === 'sink' ? interpolate(p, [0, 1], [-2.5, 2.5]) : 0;
  const rotY = interpolate(p, [0, 1], [-5, 5]);
  const sweep = interpolate(frame, [0, Math.max(30, dur)], [-40, 140]);
  return (
    <AbsoluteFill style={{background: '#050403'}}>
      <AbsoluteFill style={{transform: bgT}}>
        <Img src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(26px) brightness(0.42) saturate(0.9)', transform: 'scale(1.15)'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{perspective: 1600, alignItems: 'center', justifyContent: 'center'}}>
        <div
          style={{
            width: '90%',
            height: '66%',
            transform: `translate(${fgX}%, ${fgY}%) scale(${fgS}) rotateY(${rotY}deg)`,
            boxShadow: '0 40px 90px rgba(0,0,0,0.75)',
            position: 'relative',
            overflow: 'hidden',
            borderRadius: 6,
          }}
        >
          <Img src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `linear-gradient(110deg, rgba(255,255,255,0) ${sweep - 25}%, rgba(255,232,180,0.35) ${sweep}%, rgba(255,255,255,0) ${sweep + 25}%)`,
              mixBlendMode: 'overlay',
            }}
          />
        </div>
      </AbsoluteFill>
      <Particles seed={`${seed}dust`} kind="dust" count={28} />
    </AbsoluteFill>
  );
};

export const Shot: React.FC<{shot: ShotData; dur: number; showBadges: boolean}> = ({shot, dur, showBadges}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const fx = new Set(shot.fx);

  // ---------- transition IN ----------
  let opacity = 1;
  let inT = '';
  let inFilter = '';
  let blackUnder = 0;
  switch (shot.tr) {
    case 'dissolve':
      opacity = interpolate(frame, [0, 16], [0, 1], {extrapolateRight: 'clamp'});
      break;
    case 'dip':
      blackUnder = interpolate(frame, [0, 7], [0, 1], {extrapolateRight: 'clamp'});
      opacity = interpolate(frame, [7, 22], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
      break;
    case 'zoom': {
      const sp = spring({frame, fps, config: {damping: 16, stiffness: 160}});
      inT = `scale(${interpolate(sp, [0, 1], [1.35, 1])})`;
      opacity = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
      const b = interpolate(frame, [0, 9], [14, 0], {extrapolateRight: 'clamp'});
      inFilter = b > 0.2 ? `blur(${b}px)` : '';
      break;
    }
    case 'whip': {
      const x = interpolate(frame, [0, 9], [100, 0], {extrapolateRight: 'clamp', easing: (t) => 1 - Math.pow(1 - t, 3)});
      inT = `translateX(${x}%)`;
      const b = interpolate(frame, [0, 9], [18, 0], {extrapolateRight: 'clamp'});
      inFilter = b > 0.2 ? `blur(${b}px)` : '';
      break;
    }
    default:
      break;
  }

  const cam = cameraTransform(shot.mv, frame, dur, fps, shot.id);
  const shakeT = fx.has('shake') ? shake(frame, shot.id, 26, 90) : '';

  let content: React.ReactNode = null;
  if (shot.kind === 'video' && shot.file) {
    content = (
      <AbsoluteFill style={{transform: cam}}>
        <OffthreadVideo src={staticFile(shot.file)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
    );
  } else if (shot.kind === 'image' && shot.file) {
    content = <ParallaxImage file={shot.file} mv={shot.mv} dur={dur} seed={shot.id} />;
  } else if (shot.src === 'gfx:keys') {
    content = <GoldenKeys seed={shot.id} />;
  }

  return (
    <AbsoluteFill>
      {blackUnder > 0 ? <AbsoluteFill style={{background: '#000', opacity: blackUnder}} /> : null}
      <AbsoluteFill style={{opacity, transform: inT, filter: inFilter || undefined}}>
        <AbsoluteFill style={{transform: shakeT}}>
          {content}
          {fx.has('cracks') ? <EarthCracks seed={shot.id} /> : null}
        </AbsoluteFill>
        {fx.has('glow') ? <Glow /> : null}
        {fx.has('rays') && shot.src !== 'gfx:keys' ? <LightRays intensity={0.8} /> : null}
        {fx.has('gold') && shot.src !== 'gfx:keys' ? <Particles seed={`${shot.id}g`} kind="gold" count={30} /> : null}
        {fx.has('dust') ? <Particles seed={`${shot.id}d`} kind="dust" count={fx.has('cracks') ? 70 : 34} /> : null}
        {fx.has('pattern') ? <IslamicPattern opacity={0.13} /> : null}
        {fx.has('lightning') ? <Lightning seed={shot.id} /> : null}
      </AbsoluteFill>
      {shot.tr === 'flash' ? <LightFlash frame={frame} /> : null}
      {showBadges && shot.badge ? <VerseBadge ar={shot.badge[0]} uz={shot.badge[1]} dur={dur} /> : null}
    </AbsoluteFill>
  );
};
