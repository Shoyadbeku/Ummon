import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {TOTAL_SEC} from './storyboard';
import {FPS} from './theme';

// Main: 16:9 (1920x1080), no burned-in captions.
// Vertical: 9:16 (1080x1920) Shorts/Reels/TikTok version with word-by-word captions.
export const Root: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={Math.round(TOTAL_SEC * FPS)} fps={FPS} width={1920} height={1080} defaultProps={{captions: false}} />
    <Composition id="Vertical" component={Main} durationInFrames={Math.round(TOTAL_SEC * FPS)} fps={FPS} width={1080} height={1920} defaultProps={{captions: true}} />
  </>
);
