import React from 'react';
import {Composition} from 'remotion';
import {TarixVideo, totalFrames} from './TarixVideo';
import {VIDEO} from './config';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="TarixVideo"
    component={TarixVideo}
    durationInFrames={totalFrames(VIDEO.fps)}
    fps={VIDEO.fps}
    width={VIDEO.width}
    height={VIDEO.height}
  />
);
