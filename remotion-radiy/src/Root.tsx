import React from 'react';
import {Composition} from 'remotion';
import {Video, FPS} from './Video';
import scenes from '../public/scenes.json';
export const Root: React.FC = () => (
  <Composition id="RadiyQizlari" component={Video} durationInFrames={Math.round(scenes.total * FPS)}
    fps={FPS} width={1080} height={1920} />
);
