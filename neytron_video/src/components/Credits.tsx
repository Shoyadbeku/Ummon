import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, condensed, sans} from '../theme';
import {CREDIT_SOURCES} from '../data/sources';

/** FOOTAGE SOURCES / VIDEO MANBALARI roll. */
export const Credits: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  // content is on screen from the first to the last frame: starts low, ends with the footer still visible
  const contentH = CREDIT_SOURCES.length * 84 + 420;
  const y = interpolate(frame, [0, durationInFrames], [260, Math.min(160, 1080 - contentH - 120)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const op = interpolate(frame, [0, 15, durationInFrames - 15, durationInFrames], [0, 1, 1, 0]);
  return (
    <AbsoluteFill style={{background: '#050506', opacity: op}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center'}}>
        <div style={{fontFamily: condensed, fontSize: 30, letterSpacing: 10, color: C.red}}>FOOTAGE SOURCES</div>
        <div style={{fontFamily: condensed, fontWeight: 700, fontSize: 80, color: C.ink, marginBottom: 60}}>VIDEO MANBALARI</div>
        {CREDIT_SOURCES.map((c, i) => (
          <div key={i} style={{marginBottom: 26}}>
            <div style={{fontFamily: sans, fontWeight: 600, fontSize: 32, color: C.ink}}>{c.name}</div>
            <div style={{fontFamily: sans, fontSize: 22, color: C.dim}}>{c.detail}</div>
          </div>
        ))}
        <div style={{fontFamily: sans, fontSize: 24, color: C.dim, marginTop: 60, maxWidth: 1200, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.5}}>
          Grafik rekonstruksiyalar va xaritalar illyustratsiya bo‘lib, arxiv kadri emas. Barcha havolalar video tavsifida.
        </div>
      </div>
    </AbsoluteFill>
  );
};
