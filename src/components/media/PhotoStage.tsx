import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp} from '../../lib/anim';
import {useScene} from '../../lib/scene-context';
import {useCard} from '../../lib/layout';


export type StageCamera = {scale: number; originX: number; originY: number};

/**
 * AI rasmlar uchun "sahna": orqada xiralashtirilgan to'liq ekranli rasm,
 * oldinda oq stiker chegarali karta (Ken Burns + parallaks),
 * bir nechta rasm bo'lsa — `switchAt` kadrlarida silliq almashinadi.
 */
export const PhotoStage: React.FC<{
  /** images[i] ko'rsatila boshlaydigan kadrlar (images[0] uchun kerak emas) */
  switchAt?: number[];
  /** Kamera: zoom va fokus nuqtasi (masalan, palovga yaqinlashish) */
  camera?: (frame: number, imageIndex: number) => StageCamera;
  /** Rang/harorat effekti (CSS filter) */
  filter?: string;
  /** Kartaning ichidagi qatlamlar (karta bilan birga harakatlanadi) */
  inCard?: React.ReactNode;
  tilt?: number;
  accent: string;
}> = ({switchAt = [], camera, filter, inCard, tilt = -1.2, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {timing} = useScene();
  const CARD = useCard();
  const images = timing.images;
  if (images.length === 0) return null;

  const enter = spring({frame, fps, config: {damping: 15, stiffness: 80}});
  const progress = frame / Math.max(1, timing.durationInFrames);

  const indexAt = (f: number) => {
    let idx = 0;
    switchAt.forEach((s, i) => {
      if (f >= s && i + 1 < images.length) idx = i + 1;
    });
    return idx;
  };
  const current = indexAt(frame);
  const switchFrame = current > 0 ? switchAt[current - 1] : -1000;
  const fadeIn = interpolate(frame - switchFrame, [0, 12], [0, 1], clamp);

  const renderImage = (idx: number, opacity: number) => {
    const cam = camera?.(frame, idx) ?? {
      scale: interpolate(progress, [0, 1], [1.03, 1.13]),
      originX: 50,
      originY: 55,
    };
    return (
      <Img
        key={idx}
        src={staticFile(images[idx])}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          opacity,
          transform: `scale(${cam.scale})`,
          transformOrigin: `${cam.originX}% ${cam.originY}%`,
          filter,
        }}
      />
    );
  };

  // Parallaks: fon sekin, karta o'rtacha tezlikda siljiydi
  const bgShift = interpolate(progress, [0, 1], [30, -30]);
  const cardShift = interpolate(progress, [0, 1], [12, -12]);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{overflow: 'hidden', opacity: 0.55 * enter}}>
        <Img
          src={staticFile(images[current])}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `translateX(${bgShift}px) scale(1.25)`,
            filter: `blur(36px) saturate(1.2) ${filter ?? ''}`,
          }}
        />
        <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(7,10,20,0.35), rgba(7,10,20,0.9))'}} />
      </AbsoluteFill>

      <div
        style={{
          position: 'absolute',
          left: CARD.x,
          top: CARD.y,
          width: CARD.w,
          height: CARD.h,
          borderRadius: 30,
          padding: 10,
          background: '#FFFFFF',
          boxShadow: `0 50px 120px rgba(0,0,0,0.6), 0 0 140px ${accent}40`,
          opacity: interpolate(enter, [0, 0.4], [0, 1], clamp),
          transform: `translateX(${cardShift}px) translateY(${(1 - enter) * 120}px) scale(${0.9 + enter * 0.1}) rotate(${tilt + (1 - enter) * -4}deg)`,
        }}
      >
        <div style={{position: 'relative', width: '100%', height: '100%', borderRadius: 22, overflow: 'hidden', background: '#1A1208'}}>
          {current > 0 && fadeIn < 1 && renderImage(current - 1, 1)}
          {renderImage(current, current > 0 ? fadeIn : 1)}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(180deg, rgba(0,0,0,0) 60%, rgba(7,10,20,0.45) 100%)',
            }}
          />
          {inCard}
        </div>
      </div>
    </AbsoluteFill>
  );
};
