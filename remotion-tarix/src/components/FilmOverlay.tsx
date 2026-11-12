import React from 'react';
import {AbsoluteFill, random, useCurrentFrame} from 'remotion';

// Vinyetka + plyonka donadorligi + changlar + iliq rang
export const FilmOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2);
  const specks = new Array(14).fill(0).map((_, i) => {
    const r = random(`speck-${seed}-${i}`);
    return {
      show: r > 0.72,
      x: random(`x-${seed}-${i}`) * 100,
      y: random(`y-${seed}-${i}`) * 100,
      s: 1 + random(`s-${seed}-${i}`) * 3,
      o: 0.15 + random(`o-${seed}-${i}`) * 0.35,
    };
  });
  const scratchX = random(`scr-${Math.floor(frame / 9)}`) * 100;
  const showScratch = random(`scs-${Math.floor(frame / 9)}`) > 0.75;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {/* iliq rang tusi */}
      <AbsoluteFill style={{background: 'rgba(120, 80, 30, 0.10)', mixBlendMode: 'multiply'}} />
      {/* donadorlik */}
      <AbsoluteFill style={{opacity: 0.09, mixBlendMode: 'overlay'}}>
        <svg width="100%" height="100%">
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 30} />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#grain)" />
        </svg>
      </AbsoluteFill>
      {/* changlar */}
      {specks.map((sp, i) =>
        sp.show ? (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${sp.x}%`,
              top: `${sp.y}%`,
              width: sp.s,
              height: sp.s,
              borderRadius: '50%',
              background: '#fff',
              opacity: sp.o,
            }}
          />
        ) : null
      )}
      {showScratch ? (
        <div style={{position: 'absolute', left: `${scratchX}%`, top: 0, bottom: 0, width: 1, background: 'rgba(255,255,255,0.12)'}} />
      ) : null}
      {/* vinyetka */}
      <AbsoluteFill
        style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 85%, rgba(0,0,0,0.85) 100%)'}}
      />
      {/* pastki qorong'ulik (subtitr o'qilishi uchun) */}
      <AbsoluteFill style={{background: 'linear-gradient(to top, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 32%)'}} />
    </AbsoluteFill>
  );
};
