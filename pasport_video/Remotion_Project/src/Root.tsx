import React from 'react';
import {Composition} from 'remotion';
import {Documentary, TOTAL_FRAMES} from './Documentary';
import {FPS} from './theme';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Documentary"
    component={Documentary}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
