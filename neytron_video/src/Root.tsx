import React from 'react';
import {Composition} from 'remotion';
import {Documentary} from './Documentary';
import {FPS, TOTAL_SECONDS} from './data/timing';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Documentary"
    component={Documentary}
    durationInFrames={Math.ceil(TOTAL_SECONDS * FPS)}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
