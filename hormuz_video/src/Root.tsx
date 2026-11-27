import React from 'react';
import {Composition} from 'remotion';
import {Hormuz} from './compositions/Hormuz';
import sb from './data/storyboard.json';
export const RemotionRoot: React.FC = () => (
  <Composition id="Hormuz" component={Hormuz} durationInFrames={Math.round(sb.duration * sb.fps)} fps={sb.fps} width={1920} height={1080} />
);
