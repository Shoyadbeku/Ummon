import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {StarOrnament} from './IslamicPattern';
import {AMIRI as amiri, CORMORANT as cormorant} from '../fonts';

/**
 * Small verse-reference plate (surah + ayah number only). It is a graphic reference,
 * not a subtitle: none of the narration is written on screen.
 * Positioned top-centre, clear of the player controls at the bottom of a 16:9 frame.
 */
export const VerseBadge: React.FC<{ar: string; uz: string; dur: number}> = ({ar, uz, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const inn = spring({frame: frame - 6, fps, config: {damping: 18}});
  const out = interpolate(frame, [Math.min(dur - 12, 110), Math.min(dur, 125)], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o = inn * out;
  const line = interpolate(inn, [0, 1], [0, 220]);
  return (
    <div
      style={{
        position: 'absolute',
        top: 70,
        left: 0,
        right: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        opacity: o,
        transform: `translateY(${(1 - inn) * 18}px)`,
        filter: 'drop-shadow(0 4px 18px rgba(0,0,0,0.85))',
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        <div style={{width: line, height: 2, background: 'linear-gradient(90deg, transparent, #e6b85c)'}} />
        <StarOrnament size={34} />
        <div style={{width: line, height: 2, background: 'linear-gradient(270deg, transparent, #e6b85c)'}} />
      </div>
      <div style={{fontFamily: amiri, fontSize: 56, color: '#f6dfa4', direction: 'rtl', marginTop: 8, lineHeight: 1.25}}>{ar}</div>
      <div style={{fontFamily: cormorant, fontSize: 30, letterSpacing: 6, color: '#e9d7b0', textTransform: 'uppercase', marginTop: 2}}>{uz}</div>
    </div>
  );
};
