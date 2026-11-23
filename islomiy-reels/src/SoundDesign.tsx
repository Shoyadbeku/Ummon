import React from 'react';
import {Audio, interpolate, Sequence, staticFile} from 'remotion';
import type {ShotData} from './types';

type Cue = {at: number; file: string; vol: number; len: number};

/**
 * Sound design is derived from the edit itself so every effect lands on a visual event.
 * The narration is the hero: effects sit 14–25 dB below it, no music is used,
 * only a quiet desert-wind bed for atmosphere.
 */
export const buildCues = (shots: ShotData[]): Cue[] => {
  const cues: Cue[] = [];
  shots.forEach((s, i) => {
    const fx = new Set(s.fx);
    if (s.tr === 'whip' || s.tr === 'zoom') cues.push({at: s.start - 0.3, file: `whoosh_${(i % 2) + 1}.wav`, vol: 0.22, len: 1.6});
    if (s.tr === 'flash') cues.push({at: s.start - 0.05, file: 'soft_hit.wav', vol: 0.3, len: 2.2});
    if (s.tr === 'dip' && i % 3 === 0) cues.push({at: s.start - 0.4, file: 'whoosh_3.wav', vol: 0.1, len: 1.6});
    if (fx.has('cracks')) {
      cues.push({at: s.start, file: 'impact.wav', vol: fx.has('shake') ? 0.5 : 0.3, len: 3});
      cues.push({at: s.start + 0.1, file: 'rumble.wav', vol: fx.has('shake') ? 0.42 : 0.25, len: 8});
    }
    if (fx.has('lightning')) cues.push({at: s.start + 0.4, file: 'thunder.wav', vol: 0.26, len: 5});
    if (fx.has('keys')) {
      cues.push({at: s.start + 0.1, file: 'shimmer.wav', vol: 0.3, len: 2.5});
      cues.push({at: s.start + 1.0, file: 'shimmer.wav', vol: 0.2, len: 2.5});
    } else if (fx.has('gold') && s.tr !== 'dissolve') {
      cues.push({at: s.start + 0.05, file: 'shimmer.wav', vol: 0.16, len: 2.5});
    }
  });
  // tension risers into the two "swallowing" moments
  cues.push({at: 296.6, file: 'riser.wav', vol: 0.22, len: 3});
  cues.push({at: 16.6, file: 'riser.wav', vol: 0.16, len: 3});
  return cues.filter((c) => c.at >= 0);
};

export const SoundDesign: React.FC<{shots: ShotData[]; fps: number; duration: number}> = ({shots, fps, duration}) => {
  const cues = buildCues(shots);
  const total = Math.round(duration * fps);
  const LOOP = 64 * fps;
  const loops = Math.ceil(total / LOOP);
  return (
    <>
      {/* desert wind bed, faded in/out, looped */}
      {new Array(loops).fill(0).map((_, i) => (
        <Sequence key={`w${i}`} from={i * LOOP} durationInFrames={LOOP} layout="none">
          <Audio
            src={staticFile('sfx/wind_amb.wav')}
            volume={(f) => {
              const g = f + i * LOOP;
              return 0.07 * interpolate(g, [0, 45, total - 60, total], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            }}
          />
        </Sequence>
      ))}
      {cues.map((c, i) => (
        <Sequence key={i} from={Math.round(c.at * fps)} durationInFrames={Math.round(c.len * fps)} layout="none">
          <Audio src={staticFile(`sfx/${c.file}`)} volume={c.vol} />
        </Sequence>
      ))}
    </>
  );
};
