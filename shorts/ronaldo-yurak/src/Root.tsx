import React from 'react';
import { Composition } from 'remotion';
import '@fontsource/anton/400.css';
import '@fontsource/montserrat/600.css';
import '@fontsource/montserrat/800.css';
import { Main } from './Main';
import { FPS, TOTAL_FRAMES } from './timeline';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1080}
    height={1920}
  />
);
