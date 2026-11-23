import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import storyboard from './data/storyboard.json';
import cues from './data/subtitles.json';
import type {Cue, Scene} from './types';
import {CinematicOverlay} from './components/Common';
import {CompareScene, PhotoScene, StatScene, StatementScene, TitleScene, VideoScene} from './components/Scenes';
import {Subtitles} from './components/Subtitles';

const XFADE = 12; // frames of cross-dissolve between scenes

const SceneSwitch: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  switch (scene.kind) {
    case 'video':
      return <VideoScene scene={scene} dur={dur} />;
    case 'photo':
      return <PhotoScene scene={scene} dur={dur} />;
    case 'title':
      return <TitleScene scene={scene} dur={dur} />;
    case 'stat':
      return <StatScene scene={scene} dur={dur} />;
    case 'compare':
      return <CompareScene scene={scene} dur={dur} />;
    default:
      return <StatementScene scene={scene} dur={dur} />;
  }
};

const Fader: React.FC<{dur: number; first: boolean; children: React.ReactNode}> = ({dur, first, children}) => {
  const frame = useCurrentFrame();
  const o = first ? 1 : interpolate(frame, [0, XFADE], [0, 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

export const Documentary: React.FC = () => {
  const {fps, durationInFrames} = useVideoConfig();
  const scenes = storyboard.scenes as Scene[];
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {scenes.map((s, i) => {
        const from = Math.round(s.start * fps);
        const end = i === scenes.length - 1 ? durationInFrames : Math.round(scenes[i + 1].start * fps) + XFADE;
        const dur = Math.max(1, end - from);
        return (
          <Sequence key={s.id} from={from} durationInFrames={dur} name={`${s.id} ${s.kind}`}>
            <Fader dur={dur} first={i === 0}>
              <SceneSwitch scene={s} dur={dur} />
            </Fader>
          </Sequence>
        );
      })}
      <CinematicOverlay />
      <Subtitles cues={cues as Cue[]} />
      <Audio src={staticFile('audio/final_mix.m4a')} />
    </AbsoluteFill>
  );
};
