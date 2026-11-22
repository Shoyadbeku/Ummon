import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {TOTAL_SEC} from './storyboard';
import {FPS, H, W} from './theme';

export const Root: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={Math.round(TOTAL_SEC * FPS)} fps={FPS} width={W} height={H} />
  </>
);
