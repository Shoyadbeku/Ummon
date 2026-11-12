import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {serif, sans} from '../fonts';
import {VIDEO} from '../config';

export const Intro: React.FC<{image: string}> = ({image}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const title = VIDEO.title.split('');
  const sub = spring({frame: frame - fps * 1.2, fps, config: {damping: 200}});
  const line = spring({frame: frame - fps * 0.8, fps, config: {damping: 200}});
  const out = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const bgIn = interpolate(frame, [0, fps * 1.5], [0, 0.45], {extrapolateRight: 'clamp'});
  const sweep = interpolate(frame, [fps * 0.6, fps * 2.4], [-30, 130], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{backgroundColor: '#050403', opacity: out}}>
      <Img
        src={staticFile(image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          opacity: bgIn,
          filter: 'blur(6px) sepia(0.4) brightness(0.6)',
          transform: `scale(${1.15 + frame * 0.0008})`,
        }}
      />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,0.9) 100%)'}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <div style={{fontFamily: sans, fontWeight: 600, fontSize: 26, letterSpacing: 12, color: VIDEO.accent, opacity: line, marginBottom: 20}}>
          TARIXIY HUJJATLI FILM
        </div>
        <div style={{position: 'relative', fontFamily: serif, fontWeight: 900, fontSize: 168, color: VIDEO.text, letterSpacing: 18, whiteSpace: 'pre'}}>
          {title.map((ch, i) => {
            const s = spring({frame: frame - 4 - i * 2.5, fps, config: {damping: 14, mass: 0.6}});
            return (
              <span key={i} style={{display: 'inline-block', opacity: s, transform: `translateY(${(1 - s) * 50}px)`, filter: `blur(${(1 - s) * 8}px)`}}>
                {ch}
              </span>
            );
          })}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `linear-gradient(100deg, transparent ${sweep - 12}%, rgba(255,230,170,0.55) ${sweep}%, transparent ${sweep + 12}%)`,
              mixBlendMode: 'overlay',
            }}
          />
        </div>
        <div style={{width: 520 * line, height: 3, background: VIDEO.accent, margin: '28px 0'}} />
        <div
          style={{
            fontFamily: serif,
            fontWeight: 700,
            fontStyle: 'italic',
            fontSize: 54,
            color: VIDEO.text,
            opacity: sub,
            transform: `translateY(${(1 - sub) * 20}px)`,
          }}
        >
          {VIDEO.subtitle}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
