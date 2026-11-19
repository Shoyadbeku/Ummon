import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {FPS, DURATION_S, W, H} from './data/timing';

export const Root: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={Math.round(DURATION_S * FPS)} fps={FPS} width={W} height={H} />
);
