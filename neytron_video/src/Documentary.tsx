import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {SCENES} from './data/storyboard';
import {FPS, NARRATION_OFFSET, CREDITS_SECONDS, NARRATION_SECONDS} from './data/timing';
import {Scene, Visual} from './data/types';
import {Media} from './components/Media';
import {Card, DateCard, FamilyTree, MapScene, Molecule, Question, Reconstruction, Split, Stat, Timeline} from './components/Graphics';
import {FilmLook, LowerThird, SourceLabel} from './components/Overlays';
import {Subtitles} from './components/Subtitles';
import {Credits} from './components/Credits';

const FADE = 10; // frames of cross-dissolve between scenes

const VisualView: React.FC<{v: Visual}> = ({v}) => {
  switch (v.kind) {
    case 'video':
      return <Media file={v.file} fit={v.fit} move={v.move} video={{from: v.from, rate: v.rate}} />;
    case 'photo':
      return <Media file={v.file} fit={v.fit} move={v.move} />;
    case 'map':
      return <MapScene {...v} />;
    case 'card':
      return <Card {...v} />;
    case 'date':
      return <DateCard {...v} />;
    case 'tree':
      return <FamilyTree {...v} />;
    case 'timeline':
      return <Timeline {...v} />;
    case 'stat':
      return <Stat {...v} />;
    case 'question':
      return <Question {...v} />;
    case 'split':
      return <Split {...v} />;
    case 'molecule':
      return <Molecule />;
    case 'cctv':
      return <Reconstruction {...v} />;
  }
};

const FadeIn: React.FC<{children: React.ReactNode; first: boolean}> = ({children, first}) => {
  const frame = useCurrentFrame();
  const op = first ? 1 : interpolate(frame, [0, FADE], [0, 1], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{opacity: op}}>{children}</AbsoluteFill>;
};

const SceneView: React.FC<{s: Scene; i: number}> = ({s, i}) => (
  <FadeIn first={i === 0}>
    <VisualView v={s.v} />
    {s.lower && <LowerThird {...s.lower} />}
    {s.source && <SourceLabel source={s.source} />}
  </FadeIn>
);

export const Documentary: React.FC = () => {
  const off = Math.round(NARRATION_OFFSET * FPS);
  const creditsFrom = Math.round((NARRATION_OFFSET + NARRATION_SECONDS) * FPS);
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <Sequence from={off}>
        {SCENES.map((s, i) => {
          const from = Math.round(s.start * FPS);
          const next = SCENES[i + 1];
          const end = Math.round((next ? next.start : s.end) * FPS);
          return (
            <Sequence key={i} from={from} durationInFrames={Math.max(1, end - from + FADE)} name={`${i}: ${s.note.slice(0, 40)}`}>
              <SceneView s={s} i={i} />
            </Sequence>
          );
        })}
        <Subtitles />
      </Sequence>
      <Sequence from={creditsFrom} durationInFrames={Math.round(CREDITS_SECONDS * FPS)}>
        <Credits />
      </Sequence>
      <FilmLook />
      <Audio src={staticFile('audio/mix.wav')} />
    </AbsoluteFill>
  );
};
