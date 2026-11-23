import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import timeline from './timeline.json';
import type {ShotData} from './types';
import {Shot} from './Shot';
import {SoundDesign} from './SoundDesign';
import {FilmLook, Grain, Vignette} from './fx/Overlays';
import {IslamicPattern} from './fx/IslamicPattern';

export type ReelProps = {showVerseBadges: boolean};
export const reelSchemaDefaults: ReelProps = {showVerseBadges: true};

const shots = timeline.shots as unknown as ShotData[];

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const black = interpolate(frame, [durationInFrames - 50, durationInFrames - 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#000', opacity: black}} />;
};

export const IslamicReel: React.FC<ReelProps> = ({showVerseBadges}) => {
  const {fps} = useVideoConfig();
  const tail = Math.round(timeline.tail * fps);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {shots.map((s, i) => {
        const from = Math.round(s.start * fps);
        const dur = Math.round(s.end * fps) - from;
        const isLast = i === shots.length - 1;
        return (
          <Sequence key={s.id} from={from} durationInFrames={dur + (isLast ? 0 : tail)} name={`${s.id} ${s.note}`}>
            <Shot shot={s} dur={dur} showBadges={showVerseBadges} />
          </Sequence>
        );
      })}

      {/* closing geometric lock-up over the final shot */}
      <Sequence from={Math.round(513.4 * fps)}>
        <IslamicPattern opacity={0.22} reveal={60} />
      </Sequence>

      <FilmLook />
      <Vignette />
      <Grain opacity={0.07} />
      <Outro />

      <Audio src={staticFile('audio/voice_master.wav')} />
      <SoundDesign shots={shots} fps={fps} duration={timeline.duration} />
    </AbsoluteFill>
  );
};
