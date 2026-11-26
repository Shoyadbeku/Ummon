import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, sans} from '../theme';
import {CUES} from '../data/subtitles';

/** Phrase subtitles synced to the original narration, current word highlighted. */
export const Subtitles: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const cue = CUES.find((c) => t >= c.s && t < c.e);
  if (!cue) return null;
  const inOp = interpolate(t, [cue.s, cue.s + 0.12], [0, 1], {extrapolateRight: 'clamp'});
  const lift = interpolate(t, [cue.s, cue.s + 0.18], [10, 0], {extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 96,
        display: 'flex',
        justifyContent: 'center',
        opacity: inOp,
        transform: `translateY(${lift}px)`,
      }}
    >
      <div
        style={{
          maxWidth: 1380,
          textAlign: 'center',
          fontFamily: sans,
          fontWeight: 600,
          fontSize: 44,
          lineHeight: 1.28,
          color: C.ink,
          padding: '8px 22px',
          borderRadius: 8,
          background: 'rgba(0,0,0,0.42)',
          textShadow: '0 2px 6px rgba(0,0,0,0.9)',
        }}
      >
        {cue.w.map((w, i) => {
          const active = t >= w.s && t < w.e + 0.05;
          const past = t >= w.e;
          return (
            <span key={i} style={{color: active ? '#ffd86b' : past ? C.ink : 'rgba(244,241,234,0.78)'}}>
              {w.t}
              {i < cue.w.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
};
