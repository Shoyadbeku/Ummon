import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {FPS, DURATION_S} from './timeline';

export const Root: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={Math.round(DURATION_S * FPS)} fps={FPS} width={1080} height={1920} />
);
