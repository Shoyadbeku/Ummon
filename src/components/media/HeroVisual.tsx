import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {clamp} from '../../lib/anim';
import {useScene} from '../../lib/scene-context';

/**
 * AI rasm boshqaruvi.
 * public/images/<sahna-id>.(png|jpg|webp) mavjud bo'lsa — rasm "Ken Burns"
 * (sekin zoom + siljish) va parallaks bilan ko'rsatiladi; aks holda
 * `fallback` (vektor illyustratsiya) chiziladi. Shu sababli video har doim
 * render qilinadi — rasmlarni keyinroq qo'shish mumkin.
 */
export const HeroVisual: React.FC<{
  fallback: React.ReactNode;
  width: number;
  height: number;
  radius?: number;
  /** Ken Burns zoom kuchi */
  zoom?: number;
  /** Rasm ustidan qo'shimcha qatlamlar (bug', viewfinder...) */
  overlay?: React.ReactNode;
  style?: React.CSSProperties;
  filter?: string;
}> = ({fallback, width, height, radius = 40, zoom = 0.12, overlay, style, filter}) => {
  const {timing} = useScene();
  const frame = useCurrentFrame();
  const {durationInFrames} = timing;

  if (!timing.image) {
    return (
      <div style={{position: 'relative', width, height, ...style}}>
        {fallback}
        {overlay}
      </div>
    );
  }

  const scale = interpolate(frame, [0, durationInFrames], [1.04, 1.04 + zoom], clamp);
  const panX = interpolate(frame, [0, durationInFrames], [-1.5, 1.5], clamp);
  return (
    <div
      style={{
        position: 'relative',
        width,
        height,
        borderRadius: radius,
        overflow: 'hidden',
        boxShadow: '0 50px 120px rgba(0,0,0,0.55), 0 0 0 2px rgba(255,255,255,0.12)',
        ...style,
      }}
    >
      <Img
        src={staticFile(timing.image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale}) translateX(${panX}%)`,
          filter,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(180deg, rgba(7,10,20,0) 55%, rgba(7,10,20,0.55) 100%)',
        }}
      />
      {overlay}
    </div>
  );
};
