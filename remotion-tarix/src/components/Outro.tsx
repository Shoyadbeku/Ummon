import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {serif, sans} from '../fonts';
import {VIDEO} from '../config';

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const bg = interpolate(frame, [0, fps * 1.2], [0, 0.82], {extrapolateRight: 'clamp'});
  const a = spring({frame: frame - fps * 0.6, fps, config: {damping: 200}});
  const b = spring({frame: frame - fps * 1.3, fps, config: {damping: 12}});
  const end = interpolate(frame, [durationInFrames - fps, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});

  return (
    <AbsoluteFill style={{background: `rgba(5,4,3,${bg})`, alignItems: 'center', justifyContent: 'center', flexDirection: 'column', opacity: end}}>
      <div style={{fontFamily: serif, fontWeight: 900, fontSize: 96, color: VIDEO.text, opacity: a, transform: `translateY(${(1 - a) * 30}px)`}}>
        {VIDEO.channel}
      </div>
      <div style={{width: 360 * a, height: 3, background: VIDEO.accent, margin: '26px 0 40px'}} />
      <div
        style={{
          fontFamily: sans,
          fontWeight: 700,
          fontSize: 34,
          letterSpacing: 6,
          color: '#fff',
          background: '#c4302b',
          padding: '18px 46px',
          borderRadius: 10,
          transform: `scale(${b})`,
          boxShadow: '0 10px 40px rgba(0,0,0,0.6)',
        }}
      >
        OBUNA BO‘LING
      </div>
      <div style={{fontFamily: sans, fontWeight: 500, fontSize: 28, color: VIDEO.text, marginTop: 34, opacity: a, letterSpacing: 2}}>
        Tarixning yana ko‘plab sirlari oldinda
      </div>
    </AbsoluteFill>
  );
};
