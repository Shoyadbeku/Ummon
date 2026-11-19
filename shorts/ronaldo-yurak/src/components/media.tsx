import React from 'react';
import { AbsoluteFill, Easing, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame } from 'remotion';

type Range = [number, number];

/** Full-bleed stock clip with Ken-Burns push and grade. */
export const Clip: React.FC<{
  id: string;
  dur: number;
  startSec?: number;
  rate?: number;
  zoom?: Range;
  pan?: Range; // x in %
  panY?: Range;
  grade?: string;
  flip?: boolean;
}> = ({ id, dur, startSec = 0, rate = 1, zoom = [1.08, 1.22], pan = [0, 0], panY = [0, 0], grade, flip }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, dur], [0, 1], { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.quad) });
  const s = interpolate(p, [0, 1], zoom);
  const x = interpolate(p, [0, 1], pan);
  const y = interpolate(p, [0, 1], panY);
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: '#000' }}>
      <OffthreadVideo
        src={staticFile(`clips/${id}.mp4`)}
        startFrom={Math.round(startSec * 30)}
        playbackRate={rate}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${s}) translate(${x}%, ${y}%) ${flip ? 'scaleX(-1)' : ''}`,
          filter: grade ?? 'contrast(1.12) saturate(0.92) brightness(0.92)',
        }}
      />
      {/* teal/orange split-tone */}
      <AbsoluteFill
        style={{
          mixBlendMode: 'soft-light',
          background: 'linear-gradient(180deg, rgba(0,90,120,0.35) 0%, rgba(0,0,0,0) 45%, rgba(255,120,40,0.25) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

/** Photo with blurred fill + 2.5D parallax (background and foreground drift differently). */
export const Photo: React.FC<{
  src: string;
  dur: number;
  zoom?: Range;
  pan?: Range;
  panY?: Range;
  grade?: string;
  objectPosition?: string;
  contain?: boolean;
}> = ({ src, dur, zoom = [1.05, 1.18], pan = [0, 0], panY = [0, 0], grade, objectPosition = '50% 30%', contain }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, dur], [0, 1], { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  const s = interpolate(p, [0, 1], zoom);
  const x = interpolate(p, [0, 1], pan);
  const y = interpolate(p, [0, 1], panY);
  const g = grade ?? 'contrast(1.1) saturate(0.95)';
  return (
    <AbsoluteFill style={{ overflow: 'hidden', background: '#000' }}>
      <Img
        src={staticFile(`img/${src}`)}
        style={{
          position: 'absolute',
          inset: -60,
          width: 'calc(100% + 120px)',
          height: 'calc(100% + 120px)',
          objectFit: 'cover',
          filter: `blur(38px) brightness(0.45) ${g}`,
          transform: `scale(${1.15 + (s - 1) * 0.4}) translate(${-x * 0.4}%, 0)`,
        }}
      />
      <Img
        src={staticFile(`img/${src}`)}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: contain ? 'contain' : 'cover',
          objectPosition,
          filter: g,
          transform: `scale(${s}) translate(${x}%, ${y}%)`,
        }}
      />
    </AbsoluteFill>
  );
};
