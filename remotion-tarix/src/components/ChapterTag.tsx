import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {sans} from '../fonts';
import {VIDEO} from '../config';

// Bob nomi: avval markazda katta, keyin chap yuqoriga kichrayib o'tadi
export const ChapterTag: React.FC<{label: string; big: boolean}> = ({label, big}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const fadeIn = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const move = big ? interpolate(frame, [fps * 2.2, fps * 2.9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1;
  const bigOpacity = 1 - move;

  return (
    <>
      {big && bigOpacity > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: fadeIn * bigOpacity,
            background: `rgba(0,0,0,${0.35 * fadeIn * bigOpacity})`,
          }}
        >
          <div style={{textAlign: 'center'}}>
            <div style={{width: 90 * fadeIn, height: 3, background: VIDEO.accent, margin: '0 auto 26px'}} />
            <div
              style={{
                fontFamily: sans,
                fontWeight: 700,
                fontSize: 64,
                letterSpacing: interpolate(frame, [0, fps * 2.5], [4, 14]),
                color: VIDEO.text,
                textTransform: 'uppercase',
                textShadow: '0 4px 24px rgba(0,0,0,0.9)',
              }}
            >
              {label}
            </div>
            <div style={{width: 90 * fadeIn, height: 3, background: VIDEO.accent, margin: '26px auto 0'}} />
          </div>
        </div>
      ) : null}
      <div
        style={{
          position: 'absolute',
          top: 56,
          left: 70,
          opacity: move * fadeIn,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          fontFamily: sans,
          fontWeight: 600,
          fontSize: 22,
          letterSpacing: 4,
          textTransform: 'uppercase',
          color: VIDEO.text,
          textShadow: '0 2px 8px rgba(0,0,0,0.9)',
        }}
      >
        <div style={{width: 10, height: 10, background: VIDEO.accent, transform: 'rotate(45deg)'}} />
        {label}
      </div>
    </>
  );
};
