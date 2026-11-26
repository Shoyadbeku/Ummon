import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, random} from 'remotion';
import {C, condensed, sans} from '../theme';
import {Source} from '../data/types';

/** Mandatory on-screen attribution shown for as long as the footage is on screen. */
export const SourceLabel: React.FC<{source: Source}> = ({source}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const inn = spring({frame: frame - 4, fps, config: {damping: 200}, durationInFrames: 14});
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        position: 'absolute',
        right: 44,
        bottom: 34,
        opacity: inn * out,
        transform: `translateX(${(1 - inn) * 24}px)`,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: sans,
        fontSize: 19,
        color: 'rgba(255,255,255,0.88)',
        background: 'rgba(0,0,0,0.55)',
        padding: '7px 14px 7px 12px',
        borderRadius: 4,
        letterSpacing: 0.2,
        textShadow: '0 1px 2px rgba(0,0,0,0.8)',
      }}
    >
      <div style={{width: 3, height: 18, background: C.red}} />
      <span style={{fontWeight: 600}}>Manba:</span>
      <span>{source.label}</span>
      <span style={{opacity: 0.6, fontSize: 16}}>· {source.license}</span>
    </div>
  );
};

/** Documentary lower third with person name and role. */
export const LowerThird: React.FC<{name: string; role: string}> = ({name, role}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const bar = spring({frame: frame - 6, fps, config: {damping: 200}, durationInFrames: 18});
  const txt = spring({frame: frame - 12, fps, config: {damping: 200}, durationInFrames: 18});
  const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 90, top: 760, opacity: out}}>
      <div style={{height: 4, width: 420 * bar, background: C.red, marginBottom: 14}} />
      <div style={{overflow: 'hidden'}}>
        <div
          style={{
            fontFamily: condensed,
            fontWeight: 700,
            fontSize: 58,
            color: C.ink,
            textTransform: 'uppercase',
            letterSpacing: 2,
            transform: `translateY(${(1 - txt) * 70}px)`,
            textShadow: '0 4px 24px rgba(0,0,0,0.7)',
          }}
        >
          {name}
        </div>
      </div>
      <div style={{fontFamily: sans, fontSize: 26, color: C.dim, marginTop: 4, opacity: txt, textShadow: '0 2px 12px rgba(0,0,0,0.9)'}}>{role}</div>
    </div>
  );
};

/** Film grain + vignette + subtle light flicker. */
export const FilmLook: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2);
  const ox = Math.floor(random(`gx${seed}`) * 200);
  const oy = Math.floor(random(`gy${seed}`) * 200);
  const flicker = 0.03 + random(`f${seed}`) * 0.02;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <AbsoluteFill
        style={{
          background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 52%, rgba(0,0,0,0.62) 100%)',
        }}
      />
      <AbsoluteFill style={{opacity: 0.09, mixBlendMode: 'overlay'}}>
        <svg width="1920" height="1080" style={{transform: `translate(${-ox}px, ${-oy}px)`}}>
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed % 50} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="2200" height="1400" filter="url(#grain)" />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{background: '#fff', opacity: flicker * 0.25, mixBlendMode: 'soft-light'}} />
    </AbsoluteFill>
  );
};
