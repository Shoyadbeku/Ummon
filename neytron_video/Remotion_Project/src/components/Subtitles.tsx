import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Cue} from '../types';
import {FONT, WARM} from './Common';

/** Word-synced documentary subtitles built from the original voice timings */
export const Subtitles: React.FC<{cues: Cue[]}> = ({cues}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const cue = cues.find((c) => t >= c.start && t < c.end);
  if (!cue) return null;
  const o = interpolate(t, [cue.start, cue.start + 0.15, cue.end - 0.12, cue.end], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 70, display: 'flex', justifyContent: 'center', opacity: o}}>
      <div
        style={{
          maxWidth: 1500,
          padding: '14px 30px',
          borderRadius: 12,
          background: 'rgba(0,0,0,0.55)',
          backdropFilter: 'blur(6px)',
          fontFamily: FONT,
          fontSize: 44,
          fontWeight: 600,
          lineHeight: 1.3,
          color: '#fff',
          textAlign: 'center',
          textShadow: '0 2px 6px rgba(0,0,0,0.9)',
        }}
      >
        {cue.words.length
          ? cue.words.map((w, i) => {
              const active = t >= w.s && t < w.e + 0.05;
              const done = t >= w.e;
              return (
                <span key={i} style={{color: active ? WARM : done ? '#fff' : 'rgba(255,255,255,0.78)'}}>
                  {w.w}
                </span>
              );
            })
          : cue.text}
      </div>
    </div>
  );
};
