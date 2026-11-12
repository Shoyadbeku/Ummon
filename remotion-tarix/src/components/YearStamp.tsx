import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {serif, sans} from '../fonts';
import {VIDEO} from '../config';

// Matnda "1943-yil" kabi yil bo'lsa — katta animatsion sana belgisi
export const YearStamp: React.FC<{year: string; caption: string}> = ({year, caption}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame: frame - 6, fps, config: {damping: 200}});
  const out = interpolate(frame, [Math.min(durationInFrames - 20, fps * 5), Math.min(durationInFrames - 5, fps * 5.6)], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const target = parseInt(year, 10);
  const shown = Math.round(
    interpolate(frame, [6, 6 + fps * 1.1], [target - 37, target], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)})
  );
  const line = interpolate(frame, [10, 10 + fps * 0.8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

  return (
    <div style={{position: 'absolute', left: 110, top: 150, opacity: enter * out, transform: `translateX(${(1 - enter) * -40}px)`}}>
      <div style={{fontFamily: serif, fontWeight: 900, fontSize: 190, lineHeight: 1, color: VIDEO.text, letterSpacing: 6, textShadow: '0 8px 30px rgba(0,0,0,0.7)'}}>
        {shown}
      </div>
      <div style={{height: 4, width: 420 * line, background: VIDEO.accent, margin: '18px 0 16px'}} />
      <div style={{fontFamily: sans, fontWeight: 600, fontSize: 30, letterSpacing: 6, textTransform: 'uppercase', color: VIDEO.accent, textShadow: '0 2px 8px rgba(0,0,0,0.9)', maxWidth: 800}}>
        {caption}
      </div>
    </div>
  );
};
