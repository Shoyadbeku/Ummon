import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Story, StoryProps} from './Story';
import {Thumb} from './Thumb';
import data from '../public/timeline.json';

export const Root: React.FC = () => {
  const d = data as unknown as StoryProps & {durationSec: number};
  return (
    <>
    <Composition id="Thumb" component={Thumb} durationInFrames={1} fps={30} width={1920} height={1080} />
    <Composition
      id="Onoda"
      component={Story}
      durationInFrames={Math.ceil(d.durationSec * 30)}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={d}
    />
    </>
  );
};
