import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';

// 39.37 s voice-over @ 30 fps -> 1182 frames, 1080x1920 (9:16)
export const RemotionRoot: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={1182} fps={30} width={1080} height={1920} />
);
