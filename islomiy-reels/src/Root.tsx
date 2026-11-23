import React from 'react';
import {Composition} from 'remotion';
import {IslamicReel, reelSchemaDefaults} from './IslamicReel';
import timeline from './timeline.json';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="IslamicReel"
      component={IslamicReel}
      width={1920}
      height={1080}
      fps={timeline.fps}
      durationInFrames={Math.round(timeline.duration * timeline.fps)}
      defaultProps={reelSchemaDefaults}
    />
  );
};
