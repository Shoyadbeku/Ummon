import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Documentary} from './Documentary';
import storyboard from './data/storyboard.json';

const FPS = 30;

const Root: React.FC = () =>
  React.createElement(Composition, {
    id: 'Documentary',
    component: Documentary,
    durationInFrames: Math.ceil(storyboard.duration * FPS),
    fps: FPS,
    width: 1920,
    height: 1080,
  });

registerRoot(Root);
