import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {DURATION} from './timeline';

// 8:08 voice-over @ 30 fps, 1080x1920 (9:16)
export const RemotionRoot: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={Math.round(DURATION * 30)} fps={30} width={1080} height={1920} />
);
