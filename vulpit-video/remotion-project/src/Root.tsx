import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {SB} from './data';
import './fonts';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Main"
      component={Main}
      durationInFrames={SB.durationInFrames}
      fps={SB.fps}
      width={SB.width}
      height={SB.height}
    />
  </>
);
