import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {SB} from './data';
import './fonts';

export const RemotionRoot: React.FC = () => (
  <>
    {/* 16:9 landscape (default) */}
    <Composition id="Main" component={Main} durationInFrames={SB.durationInFrames} fps={SB.fps} width={1920} height={1080} />
    {/* 9:16 vertical version of the same edit */}
    <Composition id="Vertical" component={Main} durationInFrames={SB.durationInFrames} fps={SB.fps} width={1080} height={1920} />
  </>
);
