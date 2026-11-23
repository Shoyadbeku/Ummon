import React from 'react';
import {Composition} from 'remotion';
import {Documentary} from './Documentary';
import {TOTAL_SECONDS} from './data/scenes';
import {FPS, H, W} from './theme';

export const RemotionRoot: React.FC = () => (
	<Composition id="Documentary" component={Documentary} durationInFrames={TOTAL_SECONDS * FPS} fps={FPS} width={W} height={H} />
);
