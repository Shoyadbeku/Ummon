import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Main, Timeline} from './Main';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={300}
    defaultProps={{timeline: null as unknown as Timeline}}
    calculateMetadata={async () => {
      const timeline: Timeline = await fetch(staticFile('timeline.json')).then((r) => r.json());
      return {durationInFrames: Math.ceil(timeline.total * timeline.fps), props: {timeline}};
    }}
  />
);
